<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;

/**
 * Calls the internal Python chatbot API (stateless).
 * Laravel owns session + message persistence.
 */
class ChatbotService
{
    private const ALLOWED_BOTS = ['teacher', 'story'];

    /** Prior turns to send to Python (matches MAX_HISTORY_TURNS on the API). */
    private const MAX_HISTORY_TURNS = 20;

    public function chat(string $botId, string $message, array $history, ?string $userPrompt = null): array
    {
        if (! in_array($botId, self::ALLOWED_BOTS, true)) {
            throw new \InvalidArgumentException("Unknown bot_id: {$botId}");
        }

        $response = Http::baseUrl(config('services.chatbot.url'))
            ->timeout(120)
            ->acceptJson()
            ->post("/v1/bots/{$botId}/chat", array_filter([
                'message' => $message,
                'history' => $history,
                'user_prompt' => $userPrompt,
            ], fn ($v) => $v !== null));

        $response->throw();

        return $response->json();
    }

    /**
     * Build history payload for Python from stored messages.
     * Excludes the current user message; oldest first.
     *
     * @param  iterable<int, array{role: string, content: string}>  $storedMessages
     * @return list<array{role: string, content: string}>
     */
    public function buildHistoryPayload(iterable $storedMessages): array
    {
        $history = [];
        foreach ($storedMessages as $row) {
            if (! in_array($row['role'], ['user', 'assistant'], true)) {
                continue;
            }
            $history[] = [
                'role' => $row['role'],
                'content' => $row['content'],
            ];
        }

        $maxMessages = self::MAX_HISTORY_TURNS * 2;
        if (count($history) > $maxMessages) {
            $history = array_slice($history, -$maxMessages);
        }

        return $history;
    }
}
