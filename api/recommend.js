// Vercel 서버리스 함수: 여기서만 Gemini API 열쇠를 쓴다 (화면 소스에는 절대 안 보임)
// 공식 문서(https://ai.google.dev/api/generate-content) 기준: POST .../v1beta/models/{model}:generateContent?key=API_KEY

// 2026-09-29 확인: gemini-2.5-flash는 신규 사용자에게 막혀 있고(404).
// gemini-3.5-flash-lite로 generateContent 직접 테스트해서 200 응답 확인함
const MODEL = "gemini-3.5-flash-lite";
const TIMEOUT_MS = 10000; // 실패 처리 규칙과 맞춘 10초

// 조건과 후보로 프롬프트 문장을 만든다
function buildPrompt(budget, minRam, candidates) {
  var lines = [];
  lines.push("아래 노트북 후보 중에서 딱 한 대를 고르세요.");
  lines.push("조건: 예산 " + (budget === null ? "제한 없음" : budget + "원") +
    " · 최소 램 " + (minRam === null ? "제한 없음" : minRam + "GB"));
  lines.push("후보 목록(가격 낮은 순):");
  candidates.forEach(function (c, i) {
    lines.push((i + 1) + ". \"" + c.name + "\" · " + c.price + "원 · " + c.ram_gb + "GB");
  });
  lines.push("규칙: pick 값에는 위 후보 이름을 큰따옴표 안 글자 그대로, 띄어쓰기와 글자 하나까지 완전히 똑같이 복사해서 쓰세요. 절대 줄이거나 단어를 빼지 마세요.");
  lines.push("이유(reasons)는 정확히 2개 문장으로 쓰고, 각 문장에는 후보 표에 있는 price 또는 ram_gb 숫자를 하나 이상 그대로 넣으세요.");
  lines.push("후보 목록에 없는 노트북이나 이 표에 없는 정보(성능·배터리·무게·인기·품질·할인 등)는 말하지 마세요.");
  return lines.join("\n");
}

module.exports = async function handler(req, res) {
  if (req.method !== "POST") {
    res.status(405).json({ ok: false, reason: "invalid" });
    return;
  }

  var body = req.body || {};
  var budget = body.budget === undefined ? null : body.budget;
  var minRam = body.minRam === undefined ? null : body.minRam;
  var candidates = Array.isArray(body.candidates) ? body.candidates.slice(0, 5) : [];

  // 후보가 0개면 여기까지 오면 안 되지만, 방어적으로 한 번 더 막는다
  if (candidates.length === 0) {
    res.status(200).json({ ok: false, reason: "invalid" });
    return;
  }

  var apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    res.status(200).json({ ok: false, reason: "unavailable" });
    return;
  }

  var prompt = buildPrompt(budget, minRam, candidates);

  var controller = new AbortController();
  var timer = setTimeout(function () { controller.abort(); }, TIMEOUT_MS);

  try {
    var url = "https://generativelanguage.googleapis.com/v1beta/models/" + MODEL +
      ":generateContent?key=" + apiKey;

    var response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: {
          temperature: 0,
          responseMimeType: "application/json",
          responseSchema: {
            type: "OBJECT",
            properties: {
              pick: { type: "STRING" },
              reasons: {
                type: "ARRAY",
                items: { type: "STRING" },
                minItems: 2,
                maxItems: 2,
              },
            },
            required: ["pick", "reasons"],
          },
        },
      }),
    });

    clearTimeout(timer);

    if (!response.ok) {
      // 요청 한도 초과(429) 등도 여기서 걸러진다
      var errText = await response.text();
      console.error("gemini_not_ok", response.status, errText.slice(0, 500));
      res.status(200).json({ ok: false, reason: "unavailable" });
      return;
    }

    var data = await response.json();
    var text = data &&
      data.candidates &&
      data.candidates[0] &&
      data.candidates[0].content &&
      data.candidates[0].content.parts &&
      data.candidates[0].content.parts[0] &&
      data.candidates[0].content.parts[0].text;

    if (!text) {
      console.error("gemini_no_text", JSON.stringify(data).slice(0, 500));
      res.status(200).json({ ok: false, reason: "unavailable" });
      return;
    }

    var parsed;
    try {
      parsed = JSON.parse(text);
    } catch (e) {
      console.error("gemini_bad_json", text.slice(0, 500));
      res.status(200).json({ ok: false, reason: "invalid" });
      return;
    }

    // pick이 넘긴 후보 안에 있는지, reasons가 정확히 2개인지 확인한다
    var matched = candidates.some(function (c) { return c.name === parsed.pick; });
    var reasonsOk = Array.isArray(parsed.reasons) && parsed.reasons.length === 2 &&
      parsed.reasons.every(function (r) { return typeof r === "string"; });

    if (!matched || !reasonsOk) {
      console.error("gemini_mismatch", JSON.stringify(parsed));
      res.status(200).json({ ok: false, reason: "invalid" });
      return;
    }

    res.status(200).json({ ok: true, pick: parsed.pick, reasons: parsed.reasons });
  } catch (err) {
    clearTimeout(timer);
    console.error("gemini_error", err && err.name, err && err.message);
    // 타임아웃(AbortError)이나 네트워크 오류나 모두 "지금은 안내만" 쪽으로 처리
    res.status(200).json({ ok: false, reason: "unavailable" });
  }
};
