import { NextResponse } from 'next/server';

export async function GET() {
  try {
    const response = await fetch('http://localhost:8000/api/chat/sessions');
    const data = await response.json();

    if (!response.ok || data?.success === false) {
      return NextResponse.json(
        {
          status: 'error',
          sessions: null,
          error: data?.error || data?.detail || 'Failed to fetch sessions',
        },
        { status: response.status || 500 }
      );
    }

    return NextResponse.json({
      status: 'success',
      sessions: data.sessions || [],
      error: null,
    });
  } catch (error) {
    return NextResponse.json(
      {
        status: 'error',
        sessions: null,
        error: error instanceof Error ? error.message : 'An error occurred',
      },
      { status: 500 }
    );
  }
}
