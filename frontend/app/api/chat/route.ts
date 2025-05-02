import { spawn } from "child_process";
import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const { user_question } = await request.json();

  return new Promise<NextResponse>((resolve, reject) => {
    const py = spawn("python", ["./llmTogetherAI.py", user_question], {
      cwd: process.cwd(),
      env: process.env,
    });

    let stdout = "", stderr = "";

    py.stdout.on("data", (c) => (stdout += c.toString()));
    py.stderr.on("data", (c) => (stderr += c.toString()));

    py.on("close", (code) => {
      if (code !== 0) {
        console.error("Python error:", stderr);
        return reject(
          NextResponse.json({ error: "Backend error" }, { status: 500 })
        );
      }
      try {
        const payload = JSON.parse(stdout);
        return resolve(NextResponse.json(payload));
      } catch (e) {
        console.error("JSON parse error:", e, stdout);
        return reject(
          NextResponse.json({ error: "Invalid response format" }, { status: 500 })
        );
      }
    });
  });
}
