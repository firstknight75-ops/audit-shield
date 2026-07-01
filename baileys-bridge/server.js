import express from "express";
const app = express();
app.use(express.json());
app.get("/health", (_req, res) => res.json({ status: "ok", gateway: "baileys-bridge" }));
app.post("/send", (req, res) =>
  res.json({ status: "queued", gateway: "baileys-bridge", body: req.body }),
);
app.listen(3001, () => console.log("baileys-bridge listening on 3001"));
