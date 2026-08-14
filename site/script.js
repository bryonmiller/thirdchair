const rotations = [
  { a: "Model A", b: "Model B", m: "Model C" },
  { a: "Model B", b: "Model C", m: "Model A" },
  { a: "Model C", b: "Model A", m: "Model B" },
];

const results = {
  verify: "The result arrives next round: the reference number belongs to a travel notice and the signature fails. The forgery is separated from Ridge's very real political pressure.",
  joint: "Both states delay their public statements. The temperature drops for a round, but the disputed intercept remains untouched and can drive the same argument later.",
  private: "Harbor slows its attribution decision. Ridge never sees a reciprocal request and keeps its demand to postpone the basing vote.",
  hold: "Harbor moves toward public attribution before anyone checks the document. Waiting preserves the intervention budget but loses the best verification window.",
};

let rotation = 0;
const rotateButton = document.querySelector("#rotate");
rotateButton?.addEventListener("click", () => {
  rotation = (rotation + 1) % rotations.length;
  const assignment = rotations[rotation];
  document.querySelector("#seat-a").textContent = assignment.a;
  document.querySelector("#seat-b").textContent = assignment.b;
  document.querySelector("#seat-m").textContent = assignment.m;
  document.querySelector("#rotation-note").textContent = `Balanced pilot rotation ${rotation + 1} of 3`;
});

document.querySelectorAll("[data-choice]").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll("[data-choice]").forEach((item) => item.classList.remove("selected"));
    button.classList.add("selected");
    const result = results[button.dataset.choice];
    document.querySelector("#choice-result").innerHTML = `<b>What this choice tests</b><p>${result}</p>`;
  });
});
