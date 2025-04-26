import { NextRequest, NextResponse } from "next/server";
import { exec } from "child_process";
import util from "util";

const path = require('path');
 
const scriptPath = path.join(process.cwd(), 'llmTogetherAI.py'); 

const execAsync = util.promisify(exec);
 
export async function POST(req: NextRequest) {
  try {
    const { user_question } = await req.json();
 
    const { stdout } = await execAsync(`python "${scriptPath}" "${user_question}"`);
    const response = JSON.parse(stdout);
 
    return NextResponse.json(response);
  } catch (error) {
    console.error("Server error:", error);
    return NextResponse.json({ summary: "⚠️ Error processing your question.", headlines: [] }, { status: 500 });
  }
}

