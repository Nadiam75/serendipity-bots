from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.contracts import get_question_type

QuestionMode = Literal["convergent", "divergent"]
QuestionTypeId = Literal["mcq_single", "mcq_multi", "open_question", "image_mcq"]
Layout = Literal["question", "multiple_choice", "image_multiple_choice"]
AssessMode = Literal["mcq", "open"]
ScoreSegment = Literal["نوآموز", "توانمند", "پیشرو"]


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(..., min_length=1, max_length=32000)


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible request body. `model` selects the upstream model."""

    model: str | None = Field(
        default=None,
        description="Upstream model id (e.g. gpt-5.6-luna). Falls back to server default if omitted.",
    )
    messages: list[ChatMessage] = Field(..., min_length=1)


class ChatCompletionChoiceMessage(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: str


class ChatCompletionChoice(BaseModel):
    index: int = 0
    message: ChatCompletionChoiceMessage
    finish_reason: str | None = "stop"


class ChatCompletionResponse(BaseModel):
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]


class BotChatHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=32000)


class BotChatRequest(BaseModel):
    """Chat body for /v1/bots/{bot_id}/chat.

    Memory is owned by Laravel: load prior turns from DB, send them in ``history``,
    append the new user text in ``message``. Do not include the current message
    in ``history``. The API is stateless and does not persist sessions.
    """

    message: str = Field(..., min_length=1, max_length=20000)
    history: list[BotChatHistoryMessage] = Field(
        default_factory=list,
        max_length=40,
        description=(
            "Prior turns only (user | assistant), oldest first. "
            "Exclude the current message. Laravel stores and resends each request."
        ),
    )
    user_prompt: str | None = Field(
        default=None,
        max_length=20000,
        description="Optional extra instructions merged into the bot system prompt.",
    )
    image_description: str | None = Field(
        default=None,
        max_length=20000,
        description=(
            "Optional text description of the image shown to the child. "
            "When set, merged into the bot context (Laravel sends this; model does not fetch the image)."
        ),
    )
    model: str | None = Field(
        default=None,
        description="Upstream model id. Falls back to server default if omitted.",
    )
    max_output_tokens: int | None = Field(
        default=None,
        ge=1,
        le=4096,
        description="Cap generated tokens. Defaults to server MAX_OUTPUT_TOKENS (500).",
    )


class BotChatResponse(BaseModel):
    bot_id: str
    reply: str
    model: str
    history_turns_used: int = Field(
        description="Number of prior turns (user+assistant pairs) sent to the model after server-side trimming."
    )


class BotInfo(BaseModel):
    id: str
    name: str
    description: str
    chat_url: str | None = None
    assess_url: str | None = None
    generate_url: str | None = None
    fun_fact_url: str | None = None


class StoryPageMeta(BaseModel):
    """story_page.meta from contracts.json."""

    layout: Layout
    question_mode: QuestionMode
    min_selections: int | None = None
    max_selections: int | None = None
    answer_count: int | None = None
    max_words_per_answer: int | None = None
    max_characters_per_answer: int | None = None
    answer_placeholders: list[str] | None = None


class StoryPage(BaseModel):
    type: Literal["exercise"] = "exercise"
    title: str = "سؤال"
    text: str
    image_path: str | None = None
    meta: StoryPageMeta


class McqOption(BaseModel):
    id: str
    label: str | None = None
    alt: str | None = None
    image_path: str | None = None


class McqExercise(BaseModel):
    type: Literal["mcq"] = "mcq"
    question: str
    options: list[McqOption]
    correct_option_ids: list[str]
    order: int = 1
    is_required: bool = True


class ContractExerciseExample(BaseModel):
    """One item from contracts.json examples[]."""

    question_type_id: QuestionTypeId
    story_page: StoryPage
    exercise: McqExercise | None = None


class AssessMcqOption(McqOption):
    pass


class AssessSubArea(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    objectives: list[str] = Field(..., min_length=1)


class AssessArea(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    sub_areas: list[AssessSubArea] = Field(..., min_length=1)


class AssessRequest(BaseModel):
    """Assess a child's answer against each objective under each sub-area of each area."""

    areas: list[AssessArea] = Field(..., min_length=1)
    question: str = Field(..., min_length=1, max_length=20000)
    answer: str | None = Field(
        default=None,
        max_length=20000,
        description="Child's open-ended text. Required for assess_mode=open / divergent.",
    )
    question_mode: QuestionMode | None = Field(
        default=None,
        description="convergent or divergent. Derived from question_type_id if omitted.",
    )
    question_type_id: QuestionTypeId | None = Field(
        default=None,
        description="contracts.json question_types[].id (e.g. mcq_single, open_question).",
    )
    assess_mode: AssessMode | None = Field(
        default=None,
        description="mcq or open. Derived from question_type_id if omitted.",
    )
    interests: list[str] | None = Field(
        default=None,
        description="Child interests for contextual scoring (e.g. robots, animals).",
    )
    question_type: Layout | None = Field(
        default=None,
        description="story_page.meta.layout from contracts.json.",
    )
    min_selections: int | None = Field(default=None, ge=0)
    max_selections: int | None = Field(default=None, ge=0)
    answer_count: int | None = Field(default=None, ge=1)
    max_words_per_answer: int | None = Field(default=None, ge=1)
    max_characters_per_answer: int | None = Field(default=None, ge=1)
    answer_placeholders: list[str] | None = None
    story_title: str | None = Field(default=None, description="story_page.title override.")
    story_image_path: str | None = Field(default=None, description="story_page.image_path.")
    selected_option_ids: list[str] | None = Field(
        default=None,
        description="For MCQ/image MCQ: option ids the child selected.",
    )
    options: list[AssessMcqOption] | None = Field(
        default=None,
        description="For MCQ/image MCQ: available options (label, alt, or image_path).",
    )
    correct_option_ids: list[str] | None = Field(
        default=None,
        description="For MCQ: expected ids (helps scoring/feedback).",
    )
    user_prompt: str | None = Field(
        default=None,
        max_length=20000,
        description="Optional extra instructions for this assessment (appended to the user message).",
    )
    image_description: str | None = Field(
        default=None,
        max_length=20000,
        description=(
            "Optional text description of the image shown with the question. "
            "When set, appended to the assess context."
        ),
    )
    model: str | None = Field(
        default=None,
        description="Upstream model id. Falls back to server default if omitted.",
    )
    max_output_tokens: int | None = Field(
        default=None,
        ge=1,
        le=4096,
        description="Cap generated tokens. Defaults to server MAX_OUTPUT_TOKENS (500).",
    )

    @model_validator(mode="after")
    def resolve_contract_fields(self) -> "AssessRequest":
        qt = get_question_type(self.question_type_id)
        if qt:
            if self.question_mode is None:
                self.question_mode = qt["question_mode"]  # type: ignore[assignment]
            if self.assess_mode is None:
                self.assess_mode = qt["assess_mode"]  # type: ignore[assignment]
            if self.question_type is None:
                self.question_type = qt["layout"]  # type: ignore[assignment]
            if self.min_selections is None and "min_selections" in qt:
                self.min_selections = qt["min_selections"]
            if self.max_selections is None and "max_selections" in qt:
                self.max_selections = qt["max_selections"]

        if self.question_mode is None:
            self.question_mode = "divergent" if self.assess_mode == "open" else "convergent"
        if self.assess_mode is None:
            self.assess_mode = "open" if self.question_mode == "divergent" else "mcq"

        if self.assess_mode == "mcq":
            if not self.selected_option_ids:
                raise ValueError("selected_option_ids is required for assess_mode=mcq")
        elif not (self.answer and self.answer.strip()):
            raise ValueError("answer is required for assess_mode=open")

        return self


class ObjectiveAssessment(BaseModel):
    area: str
    sub_area: str
    objective: str
    status: Literal["met", "partial", "not_met"]
    score: int = Field(..., ge=0, le=5, description="Integer 0–5 alignment with the objective")
    feedback: str = Field(..., description="Short teacher-facing note in Persian")


class AssessResponse(BaseModel):
    question_mode: QuestionMode
    question_type_id: QuestionTypeId | None = None
    assess_mode: AssessMode | None = None
    assessments: list[ObjectiveAssessment]
    overall_score: int = Field(
        ...,
        ge=0,
        le=5,
        description="Rounded mean of objective scores (0–5)",
    )
    score_segment: ScoreSegment = Field(
        ...,
        description="Band from overall_score: 0–1 نوآموز, 2–3 توانمند, 4–5 پیشرو",
    )
    summary: str = Field(..., description="Overall Persian summary for the teacher")


class GeneratedMcqOption(McqOption):
    pass


class GeneratedExercise(BaseModel):
    """Contract-shaped exercise item (matches contracts.json examples[])."""

    question_type_id: QuestionTypeId
    story_page: StoryPage
    exercise: McqExercise | None = None
    sample_answer: str | None = Field(
        default=None,
        description="For divergent (open_question): model sample answer when exercise is null.",
    )


class GenerateExercisesRequest(BaseModel):
    """Generate similar exercises from a source question + answer."""

    question: str = Field(..., min_length=1, max_length=20000)
    answer: str = Field(..., min_length=1, max_length=20000)
    question_mode: QuestionMode | None = Field(
        default=None,
        description="convergent or divergent. Derived from question_type_id if omitted.",
    )
    question_type_id: QuestionTypeId | None = Field(
        default=None,
        description="contracts.json question_types[].id.",
    )
    min_selections: int | None = Field(default=None, ge=0)
    max_selections: int | None = Field(default=None, ge=0)
    answer_count: int | None = Field(default=None, ge=1)
    max_words_per_answer: int | None = Field(default=None, ge=1)
    max_characters_per_answer: int | None = Field(default=None, ge=1)
    answer_placeholders: list[str] | None = None
    story_title: str | None = None
    story_image_path: str | None = None
    interests: list[str] | None = Field(
        default=None,
        description="Optional child interests to personalize generated questions.",
    )
    count: int = Field(default=3, ge=1, le=10, description="Number of similar exercises to generate.")
    user_prompt: str | None = Field(
        default=None,
        max_length=20000,
        description="Optional extra generation instructions.",
    )
    image_description: str | None = Field(
        default=None,
        max_length=20000,
        description=(
            "Optional text description of a related image. "
            "When set, appended to the generation context."
        ),
    )
    model: str | None = Field(
        default=None,
        description="Upstream model id. Falls back to server default if omitted.",
    )
    max_output_tokens: int | None = Field(
        default=None,
        ge=1,
        le=4096,
        description="Cap generated tokens. Defaults to 3× server MAX_OUTPUT_TOKENS for generation.",
    )

    @model_validator(mode="after")
    def resolve_contract_fields(self) -> "GenerateExercisesRequest":
        qt = get_question_type(self.question_type_id)
        if qt:
            if self.question_mode is None:
                self.question_mode = qt["question_mode"]  # type: ignore[assignment]
            if self.min_selections is None and "min_selections" in qt:
                self.min_selections = qt["min_selections"]
            if self.max_selections is None and "max_selections" in qt:
                self.max_selections = qt["max_selections"]
        if self.question_mode is None:
            self.question_mode = "divergent"
        return self


class GenerateExercisesResponse(BaseModel):
    schema_version: str = "1.1"
    source_question: str
    question_type_id: QuestionTypeId | None = None
    question_mode: QuestionMode
    exercises: list[GeneratedExercise]
    model: str


class FunFactRequest(BaseModel):
    """Generate a child-friendly fun fact based on the child's interests."""

    interests: list[str] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Child interests (e.g. robots, cats, space).",
    )
    user_prompt: str | None = Field(
        default=None,
        max_length=20000,
        description="Optional extra instructions for fact generation.",
    )
    image_description: str | None = Field(
        default=None,
        max_length=20000,
        description=(
            "Optional text description of a related image. "
            "When set, appended to the fun-fact context."
        ),
    )
    model: str | None = Field(
        default=None,
        description="Upstream model id. Falls back to server default if omitted.",
    )
    max_output_tokens: int | None = Field(
        default=None,
        ge=1,
        le=4096,
        description="Cap generated tokens. Defaults to server MAX_OUTPUT_TOKENS (500).",
    )


class FunFactResponse(BaseModel):
    fact: str = Field(..., description="Short fun fact in Persian, suitable for ages 7–10.")
    related_interest: str = Field(
        ...,
        description="Which interest from the request the fact was tied to.",
    )
    interests: list[str] = Field(..., description="Echo of interests sent in the request.")
    model: str


class ContractsResponse(BaseModel):
    """Full contracts.json payload for Laravel / frontend."""

    schema_version: str
    question_modes: dict
    question_types: list[dict]
    examples: list[ContractExerciseExample]
