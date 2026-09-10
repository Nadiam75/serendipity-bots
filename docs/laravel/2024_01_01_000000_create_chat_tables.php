<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * Reference migration for Laravel-side chat memory.
 * Copy into your Laravel app and adjust table/column names as needed.
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::create('chat_sessions', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->string('bot_id', 32); // teacher | story
            $table->unsignedBigInteger('story_id')->nullable();
            $table->unsignedBigInteger('exercise_id')->nullable();
            $table->timestamps();

            $table->index(['user_id', 'bot_id']);
            $table->index(['user_id', 'story_id', 'exercise_id']);
        });

        Schema::create('chat_messages', function (Blueprint $table) {
            $table->id();
            $table->foreignUuid('session_id')->constrained('chat_sessions')->cascadeOnDelete();
            $table->string('role', 16); // user | assistant
            $table->text('content');
            $table->timestamp('created_at')->useCurrent();

            $table->index(['session_id', 'id']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('chat_messages');
        Schema::dropIfExists('chat_sessions');
    }
};
