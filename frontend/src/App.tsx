import {
  useEffect,
  useId,
  useRef,
  useState,
} from "react";
import type {
  FormEvent,
  KeyboardEvent,
} from "react";
import "./App.css";
import {
  INTENT_META,
  UI_COPY,
  buildIntentReply,
  formatIntentLabel,
  isIntent,
} from "./intents";
import type { Intent, Locale } from "./intents";

type FeedbackStatus =
  | "idle"
  | "sending"
  | "correct"
  | "incorrect";

type Message = {
  id: number;
  role: "user" | "assistant";
  text?: string;
  intent?: Intent;
  kind?: "welcome" | "reply";
  requestId?: string;
  sourceText?: string;
  feedbackStatus?: FeedbackStatus;
  showCorrection?: boolean;
  correctedIntent?: Intent;
};

type PredictionResponse = {
  request_id: string;
  intent: string;
};

type FeedbackResponse = {
  status: string;
};

const API_URL =
  import.meta.env.VITE_API_URL ??
  "http://127.0.0.1:8000";

const INTENTS =
  Object.keys(INTENT_META) as Intent[];

const WELCOME_MESSAGE: Message = {
  id: 1,
  role: "assistant",
  kind: "welcome",
};

const STORAGE_KEY = "creator-support-locale";

function readStoredLocale(): Locale {
  const saved = localStorage.getItem(STORAGE_KEY);

  if (saved === "ua" || saved === "en") {
    return saved;
  }

  return "ua";
}

function resolveAssistantText(
  message: Message,
  locale: Locale
): string {
  if (message.kind === "welcome") {
    return UI_COPY[locale].welcome;
  }

  if (message.intent) {
    return buildIntentReply(message.intent, locale);
  }

  return message.text ?? "";
}

function App() {
  const listId = useId();
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const [locale, setLocale] = useState<Locale>(readStoredLocale);
  const [messages, setMessages] = useState<Message[]>([
    WELCOME_MESSAGE,
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const copy = UI_COPY[locale];

  useEffect(() => {
    document.documentElement.lang =
      locale === "ua" ? "uk" : "en";
    localStorage.setItem(STORAGE_KEY, locale);
  }, [locale]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [messages, loading, locale]);

  const setLanguage = (next: Locale) => {
    setLocale(next);
    setError(null);
  };

  const sendMessage = async (rawMessage: string) => {
    const message = rawMessage.trim();

    if (!message || loading) {
      return;
    }

    const userMessage: Message = {
      id: Date.now(),
      role: "user",
      text: message,
    };

    setMessages((current) => [...current, userMessage]);
    setInput("");
    setError(null);
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/predict`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text: message }),
      });

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }

      const data =
        (await response.json()) as PredictionResponse;

      const intent = isIntent(data.intent)
        ? data.intent
        : ("OTHER" as Intent);

      const assistantMessage: Message = {
        id: Date.now() + 1,
        role: "assistant",
        kind: "reply",
        intent,
        requestId: data.request_id,
        sourceText: message,
        feedbackStatus: "idle",
      };

      setMessages((current) => [
        ...current,
        assistantMessage,
      ]);
    } catch (requestError) {
      console.error(requestError);
      setError(copy.serviceError);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const updateMessage = (
    id: number,
    patch: Partial<Message>
  ) => {
    setMessages((current) =>
      current.map((message) =>
        message.id === id
          ? {
              ...message,
              ...patch,
            }
          : message
      )
    );
  };

  const submitFeedback = async (
    message: Message,
    verdict: "correct" | "incorrect",
    correctedIntent?: Intent
  ) => {
    if (
      !message.requestId ||
      !message.intent
    ) {
      return;
    }

    if (
      verdict === "incorrect" &&
      !correctedIntent
    ) {
      return;
    }

    updateMessage(
      message.id,
      {
        feedbackStatus: "sending",
      }
    );

    setError(null);

    try {
      const payload = {
        request_id: message.requestId,
        verdict,
        predicted_intent:
          message.intent,
        ...(verdict === "incorrect"
          ? {
              text:
                message.sourceText ?? "",
              corrected_intent:
                correctedIntent,
            }
          : {}),
      };

      const response = await fetch(
        `${API_URL}/feedback`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify(
            payload
          ),
        }
      );

      if (!response.ok) {
        throw new Error(
          `Feedback API returned ${response.status}`
        );
      }

      const data =
        (await response.json()) as FeedbackResponse;

      if (data.status !== "recorded") {
        throw new Error(
          `Unexpected feedback status: ${data.status}`
        );
      }

      updateMessage(
        message.id,
        {
          feedbackStatus: verdict,
          showCorrection: false,
          correctedIntent,
        }
      );
    } catch (feedbackError) {
      console.error(
        feedbackError
      );

      updateMessage(
        message.id,
        {
          feedbackStatus: "idle",
        }
      );

      setError(
        copy.feedbackError
      );
    }
  };

  const handleSubmit = (
    event: FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();
    void sendMessage(input);
  };

  const handleReset = () => {
    setMessages([WELCOME_MESSAGE]);
    setError(null);
    setInput("");
    inputRef.current?.focus();
  };

  const handleKeyDown = (
    event: KeyboardEvent<HTMLTextAreaElement>
  ) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void sendMessage(input);
    }
  };

  const showSuggestions = messages.length <= 1 && !loading;

  return (
    <div className="shell">
      <div className="shell__glow shell__glow--one" aria-hidden />
      <div className="shell__glow shell__glow--two" aria-hidden />

      <main className="app">
        <header className="brand">
          <div className="brand__mark" aria-hidden>
            <span />
          </div>

          <div className="brand__copy">
            <p className="brand__name">Creator Support</p>
            <h1>{copy.title}</h1>
            <p className="brand__tagline">{copy.tagline}</p>
          </div>

          <div className="brand__aside">
            <div
              className="lang-switch"
              role="group"
              aria-label={copy.language}
            >
              <button
                type="button"
                className={
                  locale === "ua"
                    ? "lang-switch__btn is-active"
                    : "lang-switch__btn"
                }
                onClick={() => setLanguage("ua")}
                aria-pressed={locale === "ua"}
              >
                UA
              </button>
              <button
                type="button"
                className={
                  locale === "en"
                    ? "lang-switch__btn is-active"
                    : "lang-switch__btn"
                }
                onClick={() => setLanguage("en")}
                aria-pressed={locale === "en"}
              >
                EN
              </button>
            </div>

            <span className="status">
              <span className="status__dot" aria-hidden />
              {copy.online}
            </span>

            <button
              type="button"
              className="ghost-btn"
              onClick={handleReset}
              disabled={loading}
            >
              {copy.newChat}
            </button>
          </div>
        </header>

        <section
          className="chat"
          aria-labelledby={listId}
        >
          <h2 id={listId} className="sr-only">
            {copy.history}
          </h2>

          <div
            className="chat__messages"
            role="log"
            aria-live="polite"
          >
            {messages.map((message) => (
              <article
                key={message.id}
                className={`bubble bubble--${message.role}`}
              >
                <div className="bubble__meta">
                  <span className="bubble__author">
                    {message.role === "user"
                      ? copy.you
                      : copy.assistant}
                  </span>

                  {message.intent && (
                    <span
                      className={`intent intent--${message.intent.toLowerCase()}`}
                    >
                      {formatIntentLabel(
                        message.intent,
                        locale
                      )}
                    </span>
                  )}
                </div>

                <p>
                  {message.role === "assistant"
                    ? resolveAssistantText(message, locale)
                    : message.text}
                </p>

                {message.role === "assistant" &&
                  message.kind === "reply" &&
                  message.requestId &&
                  message.intent && (
                    <div className="feedback">
                      {message.feedbackStatus === "correct" ||
                      message.feedbackStatus === "incorrect" ? (
                        <span className="feedback__saved">
                          {copy.feedbackThanks}
                        </span>
                      ) : (
                        <>
                          <div className="feedback__prompt">
                            <span>
                              {copy.feedbackQuestion}
                            </span>

                            <div className="feedback__actions">
                              <button
                                type="button"
                                className="feedback__icon"
                                aria-label={copy.feedbackCorrect}
                                title={copy.feedbackCorrect}
                                disabled={
                                  message.feedbackStatus ===
                                  "sending"
                                }
                                onClick={() =>
                                  void submitFeedback(
                                    message,
                                    "correct"
                                  )
                                }
                              >
                                👍
                              </button>

                              <button
                                type="button"
                                className="feedback__icon"
                                aria-label={copy.feedbackIncorrect}
                                title={copy.feedbackIncorrect}
                                disabled={
                                  message.feedbackStatus ===
                                  "sending"
                                }
                                onClick={() =>
                                  updateMessage(
                                    message.id,
                                    {
                                      showCorrection:
                                        !message.showCorrection,
                                    }
                                  )
                                }
                              >
                                👎
                              </button>
                            </div>
                          </div>

                          {message.showCorrection && (
                            <div className="feedback__correction">
                              <select
                                value={
                                  message.correctedIntent ??
                                  ""
                                }
                                onChange={(event) =>
                                  updateMessage(
                                    message.id,
                                    {
                                      correctedIntent:
                                        event.target.value
                                          ? (event.target
                                              .value as Intent)
                                          : undefined,
                                    }
                                  )
                                }
                              >
                                <option value="">
                                  {
                                    copy.chooseCorrectIntent
                                  }
                                </option>

                                {INTENTS.filter(
                                  (intent) =>
                                    intent !==
                                    message.intent
                                ).map((intent) => (
                                  <option
                                    key={intent}
                                    value={intent}
                                  >
                                    {formatIntentLabel(
                                      intent,
                                      locale
                                    )}
                                  </option>
                                ))}
                              </select>

                              <button
                                type="button"
                                className="feedback__submit"
                                disabled={
                                  !message.correctedIntent ||
                                  message.feedbackStatus ===
                                    "sending"
                                }
                                onClick={() =>
                                  void submitFeedback(
                                    message,
                                    "incorrect",
                                    message.correctedIntent
                                  )
                                }
                              >
                                {message.feedbackStatus ===
                                "sending"
                                  ? copy.feedbackSending
                                  : copy.sendCorrection}
                              </button>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  )}
              </article>
            ))}

            {loading && (
              <article className="bubble bubble--assistant bubble--typing">
                <div className="bubble__meta">
                  <span className="bubble__author">
                    {copy.assistant}
                  </span>
                </div>
                <p
                  className="typing"
                  aria-label={copy.analyzing}
                >
                  <span />
                  <span />
                  <span />
                </p>
              </article>
            )}

            <div ref={bottomRef} />
          </div>

          {showSuggestions && (
            <div className="suggestions">
              <p className="suggestions__label">
                {copy.suggestions}
              </p>
              <div className="suggestions__list">
                {copy.prompts.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    className="chip"
                    onClick={() => {
                      void sendMessage(prompt);
                    }}
                    disabled={loading}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}

          <form className="composer" onSubmit={handleSubmit}>
            <label className="sr-only" htmlFor="chat-input">
              {copy.messageLabel}
            </label>

            <textarea
              id="chat-input"
              ref={inputRef}
              value={input}
              onChange={(event) =>
                setInput(event.target.value)
              }
              onKeyDown={handleKeyDown}
              placeholder={copy.placeholder}
              disabled={loading}
              rows={1}
            />

            <button
              type="submit"
              className="send-btn"
              disabled={loading || !input.trim()}
            >
              {copy.send}
            </button>
          </form>
        </section>
      </main>
    </div>
  );
}

export default App;
