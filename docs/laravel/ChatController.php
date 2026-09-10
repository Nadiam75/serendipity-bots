<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\ChatMessage;
use App\Models\ChatSession;
use App\Services\ChatbotService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Str;
use Illuminate\Validation\Rule;

/**
 * Example Laravel API for the Vue UI.
 * UI sends session_id + message; Laravel loads/saves history internally.
 */
class ChatController extends Controller
{
    public function __construct(private ChatbotService $chatbot) {}

    public function createSession(Request $request): JsonResponse
    {
        $data = $request->validate([
            'bot_id' => ['required', Rule::in(['teacher', 'story'])],
            'story_id' => ['nullable', 'integer'],
            'exercise_id' => ['nullable', 'integer'],
        ]);

        $session = ChatSession::create([
            'id' => (string) Str::uuid(),
            'user_id' => $request->user()->id,
            'bot_id' => $data['bot_id'],
            'story_id' => $data['story_id'] ?? null,
            'exercise_id' => $data['exercise_id'] ?? null,
        ]);

        return response()->json([
            'session_id' => $session->id,
            'bot_id' => $session->bot_id,
        ], 201);
    }

    public function sendMessage(Request $request, string $sessionId): JsonResponse
    {
        $data = $request->validate([
            'message' => ['required', 'string', 'min:1', 'max:20000'],
            'user_prompt' => ['nullable', 'string', 'max:20000'],
            'image_description' => ['nullable', 'string', 'max:20000'],
        ]);

        $session = ChatSession::query()
            ->where('id', $sessionId)
            ->where('user_id', $request->user()->id)
            ->firstOrFail();

        $stored = $session->messages()
            ->orderBy('id')
            ->get(['role', 'content'])
            ->all();

        $history = $this->chatbot->buildHistoryPayload($stored);

        $result = $this->chatbot->chat(
            botId: $session->bot_id,
            message: $data['message'],
            history: $history,
            userPrompt: $data['user_prompt'] ?? null,
            imageDescription: $data['image_description'] ?? null,
        );

        ChatMessage::insert([
            [
                'session_id' => $session->id,
                'role' => 'user',
                'content' => $data['message'],
                'created_at' => now(),
            ],
            [
                'session_id' => $session->id,
                'role' => 'assistant',
                'content' => $result['reply'],
                'created_at' => now(),
            ],
        ]);

        return response()->json([
            'session_id' => $session->id,
            'bot_id' => $session->bot_id,
            'reply' => $result['reply'],
            'model' => $result['model'] ?? null,
            'history_turns_used' => $result['history_turns_used'] ?? null,
        ]);
    }

    public function listMessages(Request $request, string $sessionId): JsonResponse
    {
        $session = ChatSession::query()
            ->where('id', $sessionId)
            ->where('user_id', $request->user()->id)
            ->firstOrFail();

        $messages = $session->messages()
            ->orderBy('id')
            ->get(['role', 'content', 'created_at']);

        return response()->json([
            'session_id' => $session->id,
            'bot_id' => $session->bot_id,
            'messages' => $messages,
        ]);
    }
}
