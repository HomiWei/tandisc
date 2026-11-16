import { useEffect, useState, type FormEvent } from "react";
import { postAsk } from "../api/client";
import { isAbortError, toUserMessage } from "../api/errors";
import { askStatusLabel } from "../api/labels";
import type { AskCitation, AskResult } from "../api/types";
import { safeHttpUrl } from "../lib/format";
import { ErrorBanner, LoadingState, Unavailable } from "./States";

function answerText(result: AskResult): string | null {
  if (result.status === "insufficient_data") {
    return result.answer ?? "当前档案没有这项数据";
  }
  return result.answer;
}

function CitationItem({ citation }: { citation: AskCitation }) {
  if (citation.text) return <li>{citation.text}</li>;
  const label = citation.label_zh ?? citation.field;
  const sourceName = citation.source_name ?? citation.name;
  const sourceUrl = safeHttpUrl(citation.source_url ?? citation.url);
  const rawUrl = citation.source_url ?? citation.url;
  if (!label && !sourceName && !rawUrl) return null;
  return (
    <li>
      {label ? <span>{label}</span> : null}
      {label && (sourceName || rawUrl) ? <span> · </span> : null}
      {sourceUrl ? (
        <a href={sourceUrl} target="_blank" rel="noreferrer">
          {sourceName ?? sourceUrl}
        </a>
      ) : (
        <span>{sourceName ?? rawUrl}</span>
      )}
      {citation.accessed_at ? <span>，访问日期 {citation.accessed_at}</span> : null}
    </li>
  );
}

export function AskPanel({
  targetType,
  targetId,
}: {
  targetType: "product" | "github_repo";
  targetId: string;
}) {
  const [question, setQuestion] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AskResult | null>(null);
  const [asked, setAsked] = useState<string | null>(null);

  useEffect(() => {
    setQuestion("");
    setPending(false);
    setError(null);
    setResult(null);
    setAsked(null);
  }, [targetType, targetId]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const text = question.trim();
    if (!text || pending) {
      if (!text) setError("请输入问题。");
      return;
    }
    setPending(true);
    setError(null);
    setResult(null);
    setAsked(text);
    try {
      const reply = await postAsk({
        target_type: targetType,
        target_id: targetId,
        question: text,
      });
      setResult(reply);
    } catch (err) {
      if (isAbortError(err)) return;
      setError(toUserMessage(err));
    } finally {
      setPending(false);
    }
  }

  const answer = result ? answerText(result) : null;

  return (
    <section className="section ask">
      <h2>追问这条记录</h2>
      <p className="muted">只根据本条已收录内容回答。</p>
      <form className="ask-form" data-testid="ask-form" onSubmit={onSubmit}>
        <label className="field" htmlFor="ask-input">
          问题
          <textarea
            id="ask-input"
            className="textarea"
            data-testid="ask-input"
            value={question}
            rows={4}
            onChange={(event) => setQuestion(event.target.value)}
          />
        </label>
        <button className="button-primary" type="submit" data-testid="ask-submit" disabled={pending}>
          {pending ? "正在提交" : "提交"}
        </button>
      </form>
      {pending ? <LoadingState label="正在回答。" /> : null}
      {error ? <ErrorBanner message={error} /> : null}
      {result ? (
        <div className="ask-result" aria-live="polite">
          {asked ? <p className="muted">问：{asked}</p> : null}
          <p className="ask-answer" data-testid="ask-answer">
            {answer ?? <Unavailable />}
          </p>
          <p className="ask-status" data-testid="ask-status" data-status={result.status ?? ""}>
            {askStatusLabel(result.status)}
          </p>
          {result.citations.length > 0 ? (
            <div className="citations">
              <h3>依据</h3>
              <ul>
                {result.citations.map((citation, index) => (
                  <CitationItem key={index} citation={citation} />
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
