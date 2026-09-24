export type Locale = "ua" | "en";

export type Intent =
  | "ACCESS_ACCOUNT"
  | "TECHNICAL_ISSUE"
  | "SCHEDULE_DEADLINE"
  | "SERVICE_INFO"
  | "CONTENT_USAGE_QUESTION"
  | "CHANGE_CANCEL"
  | "FEEDBACK_COMPLAINT"
  | "HUMAN_SUPPORT"
  | "OTHER";

type IntentMeta = {
  labelUa: string;
  labelEn: string;
  tone: "info" | "help" | "alert" | "human";
  replyUa: string;
  replyEn: string;
};

export const INTENT_META: Record<Intent, IntentMeta> = {
  ACCESS_ACCOUNT: {
    labelUa: "Доступ до акаунту",
    labelEn: "Account access",
    tone: "alert",
    replyUa:
      "Схоже, проблема з доступом до акаунту або матеріалів курсу. Перевірте email підтвердження покупки, спробуйте вийти й увійти знову. Якщо доступ до модуля все ще закритий — напишіть email, з якого оформлювали замовлення.",
    replyEn:
      "It looks like an account or course-access issue. Check your purchase confirmation email and try signing out and back in. If a module is still locked, share the email you used for the order.",
  },
  TECHNICAL_ISSUE: {
    labelUa: "Технічна проблема",
    labelEn: "Technical issue",
    tone: "alert",
    replyUa:
      "Це схоже на технічну несправність (відео, завантаження файлу, кнопка чи сторінка). Спробуйте оновити сторінку, інший браузер або очистити кеш. Якщо не допоможе — опишіть пристрій, браузер і точний урок/файл.",
    replyEn:
      "This looks like a technical issue (video, download, button, or page). Try refreshing, another browser, or clearing the cache. If it persists, tell us your device, browser, and the exact lesson or file.",
  },
  SCHEDULE_DEADLINE: {
    labelUa: "Розклад і дедлайни",
    labelEn: "Schedule & deadlines",
    tone: "info",
    replyUa:
      "Ваш запит стосується дат, розкладу чи дедлайнів курсу. Актуальні дати зазвичай є в кабінеті курсу в розділі «Розклад». Якщо потрібне перенесення — уточніть дату й назву модуля.",
    replyEn:
      "Your question is about dates, schedule, or deadlines. Check the course dashboard under Schedule. If you need a change, share the date and module name.",
  },
  SERVICE_INFO: {
    labelUa: "Інформація про сервіс",
    labelEn: "Service info",
    tone: "info",
    replyUa:
      "Ви запитуєте загальну інформацію про курс або сервіс (що входить у пакет, умови, формат). Коротко: програма, матеріали та умови доступу описані на сторінці курсу та в особистому кабінеті. Уточніть, що саме потрібно — модулі, сертифікат чи тарифи.",
    replyEn:
      "You're asking for general course or service info (what's included, terms, format). Program details and access terms are on the course page and in your dashboard. Tell us if you need modules, certificate, or pricing details.",
  },
  CONTENT_USAGE_QUESTION: {
    labelUa: "Як користуватися контентом",
    labelEn: "Content usage",
    tone: "help",
    replyUa:
      "Ви питаєте, як зрозуміти або застосувати матеріали курсу. Порада: йдіть за порядком уроків, виконуйте вправи після теорії й звіряйтеся з PDF/шаблоном до модуля. Напишіть номер уроку чи вправи — підкажу точніший крок.",
    replyEn:
      "You're asking how to understand or apply course materials. Tip: follow lessons in order, do exercises after theory, and use the module PDF/template as a checklist. Share the lesson or exercise number for a more precise tip.",
  },
  CHANGE_CANCEL: {
    labelUa: "Зміна або скасування",
    labelEn: "Change or cancel",
    tone: "info",
    replyUa:
      "Запит про зміну, перенесення чи скасування. Такі зміни оформлюються через підтримку з номером замовлення. Напишіть, що саме потрібно змінити (дата, тариф, скасування) і номер замовлення.",
    replyEn:
      "This is a change, reschedule, or cancellation request. Those are handled by support with your order number. Tell us what to change (date, plan, cancel) and your order ID.",
  },
  FEEDBACK_COMPLAINT: {
    labelUa: "Відгук або скарга",
    labelEn: "Feedback / complaint",
    tone: "human",
    replyUa:
      "Дякуємо, що поділилися відгуком. Ми фіксуємо скарги та пропозиції щодо контенту курсу. Опишіть, що саме не сподобалось або що можна покращити — передамо команді продукту.",
    replyEn:
      "Thank you for the feedback. We log complaints and suggestions about course content. Tell us what went wrong or what to improve — we'll pass it to the product team.",
  },
  HUMAN_SUPPORT: {
    labelUa: "Людська підтримка",
    labelEn: "Human support",
    tone: "human",
    replyUa:
      "Зрозумів — потрібна жива підтримка. Можете написати на support@creator.help або залиште контакт і короткий опис проблеми. Оператор відповість у робочі години.",
    replyEn:
      "Got it — you need a human agent. Email support@creator.help or leave your contact and a short problem summary. An operator will reply during business hours.",
  },
  OTHER: {
    labelUa: "Інше",
    labelEn: "Other",
    tone: "info",
    replyUa:
      "Поки що не вдалося точно визначити тему запиту. Сформулюйте коротше: доступ, техніка, розклад, контент курсу чи зміна замовлення — і я направлю вас у потрібний напрямок.",
    replyEn:
      "I couldn't confidently classify this yet. Rephrase briefly: access, technical issue, schedule, course content, or order change — and I'll route you correctly.",
  },
};

export const UI_COPY = {
  ua: {
    title: "Помічник курсу",
    tagline:
      "Intent-маршрутизація запитів про доступ, матеріали та користування контентом",
    newChat: "Новий чат",
    online: "Онлайн",
    history: "Історія розмови",
    you: "Ви",
    assistant: "Помічник",
    analyzing: "Аналізую запит",
    suggestions: "Швидкі запити",
    messageLabel: "Ваше повідомлення",
    placeholder: "Напишіть питання про курс або матеріали…",
    send: "Надіслати",
    language: "Мова",
    welcome:
      "Вітаю! Я помічник Creator Support. Допоможу з доступом до курсу, технічними питаннями та тим, як користуватися матеріалами й вправами. Напишіть запит своїми словами.",
    serviceError:
      "Сервіс тимчасово недоступний. Перевірте, що backend запущений на порту 8000.",
    feedbackQuestion:
      "Чи правильно визначено тему запиту?",
    feedbackCorrect:
      "Так, визначено правильно",
    feedbackIncorrect:
      "Ні, категорія неправильна",
    chooseCorrectIntent:
      "Оберіть правильну категорію",
    sendCorrection:
      "Надіслати виправлення",
    feedbackSending:
      "Надсилання…",
    feedbackThanks:
      "Дякую! Відгук збережено.",
    feedbackError:
      "Не вдалося зберегти відгук. Спробуйте ще раз.",
    prompts: [
      "Як правильно виконати другу вправу в модулі 1?",
      "Не розумію третій пункт інструкції в PDF",
      "Відео в уроці 3 не запускається",
      "Після оплати не відкрився доступ до курсу",
      "Коли дедлайн здачі домашнього завдання?",
    ],
  },
  en: {
    title: "Course assistant",
    tagline:
      "Intent routing for access, materials, and course content questions",
    newChat: "New chat",
    online: "Online",
    history: "Conversation history",
    you: "You",
    assistant: "Assistant",
    analyzing: "Analyzing your request",
    suggestions: "Quick prompts",
    messageLabel: "Your message",
    placeholder: "Ask about the course or materials…",
    send: "Send",
    language: "Language",
    welcome:
      "Hi! I'm the Creator Support assistant. I can help with course access, technical issues, and how to use lessons and exercises. Write your question in your own words.",
    serviceError:
      "The service is temporarily unavailable. Make sure the backend is running on port 8000.",
    feedbackQuestion:
      "Was the request classified correctly?",
    feedbackCorrect:
      "Yes, the classification is correct",
    feedbackIncorrect:
      "No, the category is incorrect",
    chooseCorrectIntent:
      "Choose the correct category",
    sendCorrection:
      "Send correction",
    feedbackSending:
      "Sending…",
    feedbackThanks:
      "Thanks! Your feedback was saved.",
    feedbackError:
      "Could not save feedback. Please try again.",
    prompts: [
      "How do I complete the second exercise in module 1?",
      "I don't understand the third step in the PDF",
      "The video in lesson 3 won't play",
      "I still don't have access after payment",
      "When is the homework deadline?",
    ],
  },
} as const;

export function isIntent(value: string): value is Intent {
  return value in INTENT_META;
}

export function formatIntentLabel(
  intent: string,
  locale: Locale = "ua"
): string {
  if (!isIntent(intent)) {
    return intent;
  }

  return locale === "ua"
    ? INTENT_META[intent].labelUa
    : INTENT_META[intent].labelEn;
}

export function buildIntentReply(
  intent: string,
  locale: Locale = "ua"
): string {
  if (!isIntent(intent)) {
    return locale === "ua"
      ? INTENT_META.OTHER.replyUa
      : INTENT_META.OTHER.replyEn;
  }

  return locale === "ua"
    ? INTENT_META[intent].replyUa
    : INTENT_META[intent].replyEn;
}
