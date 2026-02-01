import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const id = (await params).id;
    const response = await fetch(`http://localhost:8000/api/contracts/${id}/download`);
    const data = await response.json();

    if (!response.ok || data?.success === false) {
      return NextResponse.json(
        { error: data?.detail || data?.error || 'Failed to fetch download URL' },
        { status: response.status || 500 }
      );
    }

    return NextResponse.json({
      status: 'success',
      download_url: data.download_url || null,
      filename: data.filename || null,
      error: null,
    });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to fetch download URL' },
      { status: 500 }
    );
  }
}
