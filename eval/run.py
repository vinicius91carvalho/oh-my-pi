#!/usr/bin/env python3
"""Run the quality fixture against the local model and score it.

Scoring is deliberately dumb: every task in tasks.jsonl carries the substrings
that must (expect_all) or may (expect_any / min_matches) appear in a correct
answer, and a `why` line recording how I decided that answer by reading the
real repo or looking at the real image. A config that gets faster but drops a
task is rejected, so the pass count matters more than the tok/s here.
"""
import base64, json, mimetypes, os, sys, time, urllib.error, urllib.request

BASE = "http://127.0.0.1:1337"
MODEL = "Qwen3.8-27B-AWQ-5.0bpw"
TASKS = os.path.expanduser("~/tools/qwen3.8-27b/eval/tasks.jsonl")


def excerpt(spec):
    """The exact slice of the real file the question is about."""
    path = os.path.join(os.path.expanduser("~/github/vinicius91carvalho"),
                        spec["repo"], spec["path"])
    lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
    body = "\n".join(lines[spec["from"] - 1:spec["to"]])
    return f"==== {spec['repo']}/{spec['path']} (linhas {spec['from']}-{spec['to']}) ====\n{body}"


def content_for(task):
    if task["kind"] != "image":
        files = task.get("context_files") or []
        if files:
            return "\n\n".join(excerpt(f) for f in files) + "\n\n" + task["prompt"]
        return task["prompt"]
    path = os.path.expanduser(task["image"])
    mime = mimetypes.guess_type(path)[0] or "image/png"
    b64 = base64.b64encode(open(path, "rb").read()).decode()
    return [{"type": "text", "text": task["prompt"]},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}]


def ask(task, timeout=1800):
    body = {"model": MODEL,
            "messages": [{"role": "user", "content": content_for(task)}],
            "max_tokens": 700, "temperature": 0.0}
    req = urllib.request.Request(BASE + "/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read().decode('utf-8','ignore')[:200]}",
                "elapsed": round(time.time() - t0, 1)}
    return {"text": d["choices"][0]["message"]["content"],
            "usage": d.get("usage", {}), "elapsed": round(time.time() - t0, 1)}


def score(task, answer):
    """Case- and accent-insensitive substring check. Returns (passed, missing)."""
    if not answer:
        return False, ["<sem resposta>"]
    hay = answer.lower()
    for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"),
                 ("ã", "a"), ("õ", "o"), ("ç", "c"), ("â", "a"), ("ê", "e")):
        hay = hay.replace(a, b)
    missing = [t for t in task.get("expect_all", []) if t.lower() not in hay]
    any_terms = task.get("expect_any", [])
    if any_terms:
        hits = sum(1 for t in any_terms if t.lower() in hay)
        need = task.get("min_matches", 1)
        if hits < need:
            missing.append(f"<{need} de {any_terms} (achou {hits})>")
    return not missing, missing


def main(label):
    tasks = [json.loads(l) for l in open(TASKS) if l.strip()]
    results, passed = [], 0
    print(f"\n### fixture em {label}  ({len(tasks)} tarefas)\n")
    for t in tasks:
        r = ask(t)
        ok, missing = (False, [r["error"]]) if "error" in r else score(t, r.get("text", ""))
        passed += ok
        print(f"  [{'PASSOU' if ok else 'FALHOU'}] {t['id']:<6} {t['kind']:<10} "
              f"{r['elapsed']:>6}s" + ("" if ok else f"   faltou: {missing}"))
        results.append({**t, "answer": r.get("text", r.get("error")),
                        "passed": ok, "missing": missing, "elapsed": r["elapsed"],
                        "usage": r.get("usage")})
    out = {"config": label, "passed": passed, "total": len(tasks), "tasks": results}
    path = os.path.expanduser(f"~/tools/qwen3.8-27b/eval/fixture-{label}.json")
    json.dump(out, open(path, "w"), indent=2, ensure_ascii=False)
    by_kind = {}
    for r in results:
        k = by_kind.setdefault(r["kind"], [0, 0])
        k[0] += r["passed"]; k[1] += 1
    print(f"\n  TOTAL: {passed}/{len(tasks)}   " +
          "  ".join(f"{k}={v[0]}/{v[1]}" for k, v in sorted(by_kind.items())))
    print(f"  -> {path}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "unnamed")
