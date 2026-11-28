---
name: conversation-notes
description: Use when turning a conversation between a user and an AI agent into clear, submission-ready notes that distinguish the user's requests from the agent's responses.
argument-hint: Provide the conversation or identify the conversation to summarize, plus any required format.
---

# Conversation Notes

## Purpose

Turn a user-agent conversation into concise, readable notes that make it clear what the user asked and how the agent responded. Preserve the conversation's actual meaning and outcome without reproducing unnecessary dialogue.

## Workflow

1. Use only the conversation content available in the current context or supplied by the user. 
2. Read the full available conversation before summarizing. Identify the user's requests, the agent's responses, any follow-up questions and answers, decisions, actions, results, and unresolved points.
3. Keep each user's request distinct from the agent's response. For multi-turn discussions, organize notes in chronological exchange order or group closely related turns while preserving who said or did what.
4. Summarize faithfully and neutrally. Do not invent details, claim agreement that was not given, or present suggestions as decisions. Retain important qualifications, corrections, uncertainty, and disagreements.
5. Include tool or implementation results only when they are evidenced in the conversation. Distinguish work that was proposed from work that was actually completed or verified.
6. Make the notes easy to scan. Use plain language, descriptive headings, and concise bullets. Omit greetings and repetition unless they affect the meaning or outcome.
7. Follow any requested length or submission format. If none is specified, use the structure below.

## Default output

# Conversation Notes

**Topic:** A short description of the conversation.

## User requests and agent responses

### Exchange 1

**The user asked:**
*The request or question, summarized faithfully.*

**Agent responded:**
The answer, explanation, or proposed approach.

**Outcome:**
Any decision, action taken, result, or follow-up needed. Omit this heading if there is no distinct outcome.

Repeat the exchange section as needed. For a short conversation, combine related turns without losing attribution.

## Decisions and completed actions

List only decisions actually made and actions demonstrably completed. Omit this section if there are none.

## Open questions or follow-up

List unresolved questions or next steps. Omit this section if everything was resolved.

## Final checks

- Every request is attributed to the user and every answer to the agent.
- The order and outcome of the discussion are accurate.
- Proposed, completed, and verified work are not conflated.
- No facts or commitments have been added beyond the source conversation.
