import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { message, session_id, contract_id } = body;
    const apiKey = process.env.BACKEND_API_KEY;

    if (!message) {
      return NextResponse.json(
        {
          success: false,
          status: 'error',
          response: null,
          error: 'Message is required',
          session_id: null,
        },
        { status: 400 }
      );
    }

    let activeSessionId = session_id as string | undefined;

    if (!activeSessionId) {
      const sessionResponse = await fetch('http://localhost:8000/api/chat/session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(apiKey ? { 'X-API-Key': apiKey } : {}),
        },
      });

      const sessionData = await sessionResponse.json();
      if (!sessionResponse.ok || !sessionData.session_id) {
        return NextResponse.json(
          {
            success: false,
            status: 'error',
            response: null,
            error: sessionData?.detail || sessionData?.error || 'Failed to create session',
            session_id: null,
          },
          { status: sessionResponse.status || 500 }
        );
      }

      activeSessionId = sessionData.session_id;
    }

    const response = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(apiKey ? { 'X-API-Key': apiKey } : {}),
      },
      body: JSON.stringify({
        message,
        session_id: activeSessionId,
        contract_id: contract_id || undefined,
      }),
    });

    const data = await response.json();

    if (!response.ok || data?.success === false) {
      return NextResponse.json(
        {
          success: false,
          status: 'error',
          response: null,
          error: data?.error || data?.detail || 'Failed to process message',
          session_id: activeSessionId || null,
        },
        { status: response.status || 500 }
      );
    }

    return NextResponse.json({
      success: true,
      status: 'success',
      message: data.message || '',
      response: data.message || '',
      error: null,
      session_id: data.session_id || activeSessionId || null,
      agent: data.agent || null,
      tools_used: data.tools_used || [],
      citations: data.citations || [],
    });
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        status: 'error',
        response: null,
        error: error instanceof Error ? error.message : 'An error occurred',
        session_id: null,
      },
      { status: 500 }
    );
  }
}
