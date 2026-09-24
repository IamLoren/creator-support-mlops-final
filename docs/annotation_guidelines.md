# Annotation Guidelines

## Purpose

This document defines the annotation rules for the
Ukrainian-English Creator & SMB Customer Support Intent Dataset.

Each customer message must be assigned exactly one intent label.

The same annotation rules must be applied to both Ukrainian and English messages.

## General annotation rules

1. Assign exactly one intent to each message.
2. Choose the intent based on the user's primary goal, not only on individual keywords.
3. Use the same rules for Ukrainian and English examples.
4. If a message could belong to multiple classes, choose the class representing the main user request.
5. If none of the defined intents fits the message, use `OTHER`.
6. Ambiguous cases should be documented and used to improve these guidelines.

---

## 1. ACCESS_ACCOUNT

### Definition

Use `ACCESS_ACCOUNT` when the user's main problem is related to authentication,
account access, permissions, or access to purchased/assigned content.

### Positive examples

Ukrainian:

- "Не можу увійти у свій акаунт."
- "Після оплати мені не відкрився доступ до курсу."
- "Система пише, що в мене немає доступу до матеріалів."

English:

- "I can't log into my account."
- "I paid for the course but I still don't have access."
- "It says I don't have permission to view the materials."

### Permission-related errors

Use `ACCESS_ACCOUNT` when the message indicates that access is denied because of
permissions or authorization, including errors such as:

- `403 Forbidden`;
- "Access denied";
- "You don't have permission";
- content marked as unavailable for the current user.

Example:

> "Сайт відкривається, але другий модуль показує 403 Forbidden."

Classification:

`ACCESS_ACCOUNT`

### Do not use when

Do not use `ACCESS_ACCOUNT` if the user successfully has access to the platform
or content, but a particular technical feature does not work.

Example:

> "Я відкрив урок, але відео не запускається."

This should be classified as:

`TECHNICAL_ISSUE`

### Boundary rule

Use:

- `ACCESS_ACCOUNT` → the user **cannot gain access**
- `TECHNICAL_ISSUE` → the user **has access, but something does not work correctly**

---

## 2. TECHNICAL_ISSUE

### Definition

Use `TECHNICAL_ISSUE` when the user can access the platform, account, service, or content,
but a technical component does not work correctly.

Typical technical issues include problems with:

- video playback;
- file downloading;
- broken buttons or links;
- page loading;
- application errors;
- unexpected system behavior.

### Positive examples

Ukrainian:

- "Відео в третьому уроці не запускається."
- "Не можу завантажити PDF."
- "Кнопка «Зберегти» не працює."
- "Сторінка постійно показує помилку."

English:

- "The video in lesson three won't play."
- "I can't download the PDF."
- "The Save button doesn't work."
- "The page keeps showing an error."

### Do not use when

Do not use `TECHNICAL_ISSUE` when the main problem is that the user does not have
permission or access to the account, course, service, or materials.

Do not use `TECHNICAL_ISSUE` for explicit authentication, authorization, or
permission errors such as `401 Unauthorized` or `403 Forbidden`.

Example:

> "Пише, що в мене немає доступу до курсу."

This should be classified as:

`ACCESS_ACCOUNT`

### Boundary rule

Use:

- `ACCESS_ACCOUNT` → the user cannot access the account, service, or content;
- `TECHNICAL_ISSUE` → the user has access, but a technical feature or resource does not work correctly.

---

## 3. SCHEDULE_DEADLINE

### Definition

Use `SCHEDULE_DEADLINE` when the user's main request is about:

- date;
- time;
- schedule;
- deadline;
- duration;
- start or end time of an event;
- when something will happen or must be completed.

### Positive examples

Ukrainian:

- "Коли буде наступний вебінар?"
- "До якого числа потрібно здати домашнє завдання?"
- "О котрій починається консультація?"
- "Скільки ще буде відкритий доступ до цього модуля?"

English:

- "When is the next webinar?"
- "What is the deadline for the assignment?"
- "What time does the consultation start?"
- "How long will this module remain available?"

### Do not use when

Do not use `SCHEDULE_DEADLINE` if the user's main goal is to change or cancel an existing booking or event.

Example:

> "Можна перенести консультацію на п'ятницю?"

This should be classified as:

`CHANGE_CANCEL`

Do not use `SCHEDULE_DEADLINE` if the user is asking general information about the service rather than a specific date, time, or deadline.

Example:

> "Скільки триває весь курс?"

Depending on the dataset rules, this should usually be classified as:

`SERVICE_INFO`

### Deadline change requests

Do not use `SCHEDULE_DEADLINE` when the user asks to extend, move,
or otherwise change an existing deadline.

Example:

> "Я пропустила дедлайн. Чи можна здати завдання завтра?"

Classification:

`CHANGE_CANCEL`

### Boundary rule

Use:

- `SCHEDULE_DEADLINE` → the user wants to know **when** something happens, starts, ends, or must be completed;
- `CHANGE_CANCEL` → the user wants to **modify or cancel** an existing schedule, booking, appointment, or service;
- `SERVICE_INFO` → the user asks general descriptive information about the service or product.

---

## 4. SERVICE_INFO

### Definition

Use `SERVICE_INFO` when the user's main request is to get general information
about a product, service, program, course, package, subscription, or offer.

Typical questions include:

- what is included;
- how the service works;
- who the service is for;
- price-related or package-related information;
- general availability;
- duration of the whole service or program;
- requirements or conditions for using the service.

### Positive examples

Ukrainian:

- "Що входить у програму курсу?"
- "Чи підходить цей курс для початківців?"
- "Скільки триває весь курс?"
- "Які матеріали входять у пакет?"
- "Чи є у вас консультації англійською мовою?"

English:

- "What is included in the course?"
- "Is this program suitable for beginners?"
- "How many weeks does the course last?"
- "What materials are included in the package?"
- "Do you offer consultations in English?"

### Do not use when

Do not use `SERVICE_INFO` when the user asks about a specific scheduled event,
deadline, appointment, or date.

Example:

> "О котрій завтра починається вебінар?"

Classification:

`SCHEDULE_DEADLINE`

Do not use `SERVICE_INFO` when the user is asking how to understand,
use, or apply specific content or instructions.

Example:

> "Як правильно виконувати вправу з третього модуля?"

Classification:

`CONTENT_USAGE_QUESTION`

### Boundary rule

Use:

- `SERVICE_INFO` → the user asks **what the product/service is, includes, costs,
  offers, or how it is generally organized**;
- `SCHEDULE_DEADLINE` → the user asks **when a specific event happens
  or when something must be completed**;
- `CONTENT_USAGE_QUESTION` → the user asks **how to understand, use,
  follow, or apply specific content or instructions**.

---

## 5. CONTENT_USAGE_QUESTION

### Definition

Use `CONTENT_USAGE_QUESTION` when the user's main request is about
how to understand, use, follow, apply, or complete specific content,
instructions, materials, exercises, recommendations, or product guidance.

Typical questions include:

- how to complete an exercise;
- how to use provided materials;
- how to follow an instruction;
- what a specific part of the content means;
- how to apply a recommendation;
- clarification of educational or instructional content.

### Positive examples

Ukrainian:

- "Як правильно виконати другу вправу?"
- "Не розумію, що означає третій пункт інструкції."
- "Як використовувати цей шаблон?"
- "Як часто потрібно виконувати цю вправу?"
- "Поясніть, будь ласка, як застосувати рекомендації з PDF."

English:

- "How should I complete the second exercise?"
- "I don't understand the third step in the instructions."
- "How do I use this template?"
- "How often should I do this exercise?"
- "Can you explain how to apply the recommendations from the PDF?"

### Do not use when

Do not use `CONTENT_USAGE_QUESTION` when the user asks general information
about what a product, service, course, or package includes.

Example:

> "Що входить у програму курсу?"

Classification:

`SERVICE_INFO`

Do not use `CONTENT_USAGE_QUESTION` when the content cannot be opened,
downloaded, played, or otherwise accessed because of a technical problem.

Example:

> "PDF не завантажується."

Classification:

`TECHNICAL_ISSUE`

Do not use `CONTENT_USAGE_QUESTION` when the user has no permission
or access to the content.

Example:

> "У мене немає доступу до другого модуля."

Classification:

`ACCESS_ACCOUNT`

### Boundary rule

Use:

- `CONTENT_USAGE_QUESTION` → the user **has the content and asks how to
  understand, use, follow, or apply it**;
- `SERVICE_INFO` → the user asks **general information about the product
  or service**;
- `TECHNICAL_ISSUE` → the content or feature **does not work correctly**;
- `ACCESS_ACCOUNT` → the user **does not have permission or access**.

---

## 6. CHANGE_CANCEL

### Definition

Use `CHANGE_CANCEL` when the user's main goal is to modify, reschedule,
extend, replace, cancel, or stop an existing booking, appointment,
deadline, subscription, service, or other previously arranged condition.

Typical requests include:

- rescheduling an appointment;
- changing a date or time;
- extending a deadline;
- cancelling a booking;
- cancelling a subscription or service;
- changing previously selected options.

### Positive examples

Ukrainian:

- "Можна перенести консультацію на п'ятницю?"
- "Хочу скасувати запис на завтра."
- "Чи можна продовжити дедлайн ще на два дні?"
- "Мені потрібно змінити дату консультації."
- "Хочу відписатися від підписки."

English:

- "Can I move my appointment to Friday?"
- "I want to cancel tomorrow's booking."
- "Can you extend the deadline by two days?"
- "I need to change the consultation date."
- "I want to cancel my subscription."

### Do not use when

Do not use `CHANGE_CANCEL` when the user only asks when something is scheduled.

Example:

> "О котрій завтра консультація?"

Classification:

`SCHEDULE_DEADLINE`

Do not use `CHANGE_CANCEL` when the user only asks general information
about cancellation or rescheduling policies without requesting a change.

Example:

> "Чи можна взагалі переносити консультації?"

Classification:

`SERVICE_INFO`

### Information request vs change request

Use `SERVICE_INFO` when the user asks whether a change is possible
or asks about the rules for making a change, but does not request
the change itself.

Example:

> "Чи можна змінити email, до якого прив'язаний акаунт?"

Classification:

`SERVICE_INFO`

Use `CHANGE_CANCEL` when the user explicitly requests that an existing
setting, booking, deadline, subscription, or other arrangement be changed.

Example:

> "Змініть, будь ласка, email мого акаунта."

Classification:

`CHANGE_CANCEL`

### Boundary rule

Use:

- `CHANGE_CANCEL` → the user wants to **change or cancel something already arranged**;
- `SCHEDULE_DEADLINE` → the user only wants to know **when something happens**;
- `SERVICE_INFO` → the user asks about **general rules or policies** without requesting a concrete change.

---

## 7. FEEDBACK_COMPLAINT

### Definition

Use `FEEDBACK_COMPLAINT` when the user's main goal is to express
satisfaction, dissatisfaction, criticism, praise, or a general opinion
about the product, service, support experience, content, or platform.

Typical messages include:

- positive feedback;
- negative feedback;
- complaints;
- criticism;
- praise;
- statements about user experience.

### Positive examples

Ukrainian:

- "Мені дуже сподобався курс, особливо практичні завдання."
- "Я незадоволена якістю підтримки."
- "Це вже третій день нічого нормально не працює."
- "Матеріали дуже корисні, дякую."
- "Сервіс став набагато гіршим після останнього оновлення."

English:

- "I really liked the course, especially the practical exercises."
- "I'm unhappy with the quality of support."
- "Nothing has been working properly for three days."
- "The materials are very useful, thank you."
- "The service has become much worse since the last update."

### Do not use when

Do not use `FEEDBACK_COMPLAINT` when the user's main goal is to report
a specific technical problem and they appear to expect it to be fixed.

Example:

> "The video in lesson three won't play."

Classification:

`TECHNICAL_ISSUE`

Do not use `FEEDBACK_COMPLAINT` when the user's main goal is to request
a specific change or cancellation.

Example:

> "Скасуйте мою підписку."

Classification:

`CHANGE_CANCEL`

### Feedback combined with an action request

If a message contains feedback or dissatisfaction together with a clear
request to perform an action, classify the message by the requested action.

Example:

> "Please cancel my subscription, I'm unhappy with the service."

Classification:

`CHANGE_CANCEL`

### Boundary rule

Use:

- `FEEDBACK_COMPLAINT` → the main purpose is to **express an opinion,
  satisfaction, dissatisfaction, criticism, or praise**;
- `TECHNICAL_ISSUE` → the main purpose is to **report a concrete technical problem**;
- `CHANGE_CANCEL` → the main purpose is to **request a concrete change or cancellation**.

---

## 8. HUMAN_SUPPORT

### Definition

Use `HUMAN_SUPPORT` when the user's main goal is to explicitly request
communication with a human support agent, manager, consultant, or other
real person.

Typical requests include:

- asking to speak with a human;
- asking to contact a manager;
- requesting a support agent;
- asking for a callback;
- refusing automated assistance and requesting human help.

### Positive examples

Ukrainian:

- "З'єднайте мене, будь ласка, з оператором."
- "Я хочу поговорити з менеджером."
- "Мені потрібна допомога живої людини."
- "Передайте мій запит у підтримку."
- "Нехай мені зателефонує консультант."

English:

- "Please connect me with a support agent."
- "I want to speak to a manager."
- "I need help from a real person."
- "Please forward my request to human support."
- "Can someone call me back?"

### Do not use when

Do not use `HUMAN_SUPPORT` simply because the user has a problem that
could eventually require human assistance.

Example:

> "Не можу завантажити PDF."

Classification:

`TECHNICAL_ISSUE`

Do not use `HUMAN_SUPPORT` when the user requests a specific business action
and does not explicitly ask for a human.

Example:

> "Скасуйте мою консультацію."

Classification:

`CHANGE_CANCEL`

### Human request overrides the underlying issue

If the message contains a specific problem together with an explicit
request to speak with a human, classify it as `HUMAN_SUPPORT`.

Example:

> "Я не можу увійти в акаунт, з'єднайте мене з оператором."

Classification:

`HUMAN_SUPPORT`

### Boundary rule

Use:

- `HUMAN_SUPPORT` → the user explicitly requests **a human, operator,
  manager, consultant, callback, or human support**;
- another intent → the user describes a concrete problem or action request
  without explicitly asking to communicate with a human.

---

## 9. OTHER

### Definition

Use `OTHER` when the user's message does not fit any of the defined
customer-support intent classes.

Typical cases include:

- unrelated questions;
- casual conversation;
- spam-like or meaningless messages;
- unsupported topics;
- messages where no defined intent can be identified reliably.

### Positive examples

Ukrainian:

- "Який сьогодні курс долара?"
- "Розкажи анекдот."
- "Хто виграв учорашній матч?"
- "Привіт :)"
- "asdfgh123"

English:

- "What's the weather today?"
- "Tell me a joke."
- "Who won the game yesterday?"
- "Hi :)"
- "qwerty123"

### Do not use when

Do not use `OTHER` simply because the message is short or unusual.

Example:

> "Не працює."

If the context clearly indicates a technical problem, classify it as:

`TECHNICAL_ISSUE`

Do not use `OTHER` when one of the defined intent classes fits the user's
main goal, even if the wording is informal or contains spelling mistakes.

### Boundary rule

Use:

- `OTHER` → no existing intent matches the message reliably;
- one of the defined intents → the user's main goal can still be identified
  despite informal language, typos, or unusual phrasing.
