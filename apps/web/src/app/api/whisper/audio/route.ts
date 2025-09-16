import { NextRequest, NextResponse } from "next/server";

export async function POST(_req: NextRequest) {
  // Audio transcription disabled - Supabase removed
  return NextResponse.json(
    {
      error: "Audio transcription is currently disabled",
    },
    { status: 503 }
  );
}
