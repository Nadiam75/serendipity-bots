<?php

// config/services.php — add:

'chatbot' => [
    'url' => env('CHATBOT_API_URL', 'http://127.0.0.1:8001'),
],

// .env:
// CHATBOT_API_URL=http://127.0.0.1:8001

// routes/api.php — example:

use App\Http\Controllers\Api\ChatController;

Route::middleware('auth:sanctum')->group(function () {
    Route::post('/chat/sessions', [ChatController::class, 'createSession']);
    Route::get('/chat/sessions/{sessionId}/messages', [ChatController::class, 'listMessages']);
    Route::post('/chat/sessions/{sessionId}/messages', [ChatController::class, 'sendMessage']);
});
