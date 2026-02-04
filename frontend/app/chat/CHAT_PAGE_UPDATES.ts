/**
 * Updated Chat Page with Improvements
 * - Better error messages
 * - Loading states
 * - Timeouts
 * 
 * Apply these changes to frontend/app/chat/page.tsx
 */

// Add these imports:
// import { LoadingState } from '@/components/ui/loading-state';
// import { getErrorMessage, handleChatResponse } from '@/lib/error-messages';

// Replace the handleSubmit function with this improved version:

const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
  e.preventDefault();
  if (!input.trim() || isGenerating) return;

  const messageText = input.trim();
  // Add user message
  const userMessage = {
    id: Date.now().toString(),
    role: 'user',
    content: messageText,
  };
  setMessages((prev) => [...prev, userMessage]);
  setInput('');
  setIsGenerating(true);

  try {
    // Create timeout promise
    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Request timeout')), 35000) // 35 sec timeout
    );

    const fetchPromise = fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: messageText,
        session_id: sessionId,
      }),
    });

    // Race between fetch and timeout
    const response = await Promise.race([fetchPromise, timeoutPromise]) as Response;

    if (!response.ok) {
      // Handle HTTP errors with user-friendly messages
      const errorData = await response.json();
      const errorMessage = getErrorMessage(
        response.status,
        errorData?.error || errorData?.detail
      );

      const errorBotMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `❌ Error: ${errorMessage}`,
      };
      setMessages((prev) => [...prev, errorBotMessage]);
      setIsGenerating(false);
      return;
    }

    const data = await response.json();

    if (data.success) {
      // Store the session ID for future messages
      if (data.session_id) {
        setSessionId(data.session_id);
      }

      // Add bot response
      const botMessage = {
        id: data.session_id || Date.now().toString(),
        role: 'assistant',
        content: data.message || 'No response received',
      };
      setMessages((prev) => [...prev, botMessage]);
    } else {
      // Handle API error response
      const errorMessage = data.error || 'Something went wrong';
      const errorBotMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `❌ Error: ${errorMessage}`,
      };
      setMessages((prev) => [...prev, errorBotMessage]);
    }
  } catch (error) {
    // Handle network errors with user-friendly message
    const errorText = error instanceof Error ? error.message : 'Unknown error';
    const isTimeout = errorText.includes('timeout') || errorText.includes('too long');
    
    const errorMessage = isTimeout
      ? 'Request took too long. Try a shorter message or simpler query.'
      : 'Failed to connect to the server. Please check your connection and try again.';

    const errorBotMessage = {
      id: Date.now().toString(),
      role: 'assistant',
      content: `❌ Error: ${errorMessage}`,
    };
    setMessages((prev) => [...prev, errorBotMessage]);
    console.error('Chat error:', error);
  } finally {
    setIsGenerating(false);
  }
};

// Update the loading state in the render section:
// Replace:
//   {isGenerating && (
//     <ChatBubble variant="received">
//       <ChatBubbleAvatar src="" fallback="🤖" />
//       <ChatBubbleMessage isLoading />
//     </ChatBubble>
//   )}
//
// With:
//   {isGenerating && (
//     <ChatBubble variant="received">
//       <ChatBubbleAvatar src="" fallback="🤖" />
//       <ChatBubbleMessage>
//         <LoadingState message="AI is analyzing your question..." />
//       </ChatBubbleMessage>
//     </ChatBubble>
//   )}
