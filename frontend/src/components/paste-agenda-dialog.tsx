import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { meetingsKey } from '@/hooks/queries'
import { api, type Agenda, type Meeting, type ParsedMeeting } from '@/lib/api'

const example =
  'Порядок денний: обговорити реліз. Відповідальна Олена, 15 хвилин. Дія: підготувати чекліст, Олена, до 2026-10-30.'
const emptyItem = () => ({
  topic: '',
  owner: null,
  duration_minutes: null,
  notes: '',
  action_items: [],
})

export function PasteAgendaDialog({ meeting, onClose }: { meeting: Meeting; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [text, setText] = useState('')
  const [timezone, setTimezone] = useState(() => Intl.DateTimeFormat().resolvedOptions().timeZone)
  const [referenceDate, setReferenceDate] = useState(() =>
    format(new Date(meeting.starts_at), 'yyyy-MM-dd'),
  )
  const [draft, setDraft] = useState<Agenda | null>(() =>
    meeting.agenda ? structuredClone(meeting.agenda) : null,
  )
  const [original, setOriginal] = useState<Agenda | null>(() =>
    meeting.ai_suggestion ? structuredClone(meeting.ai_suggestion) : null,
  )
  const [result, setResult] = useState<ParsedMeeting | null>(null)
  const [error, setError] = useState('')
  const parse = useMutation({
    mutationFn: () => api.parseAgenda(meeting.id, text, timezone, referenceDate),
  })
  const save = useMutation({ mutationFn: () => api.saveAgenda(meeting.id, draft!, original) })
  const busy = parse.isPending || save.isPending
  const change = (edit: (value: Agenda) => void) => {
    if (!draft) return
    const copy = structuredClone(draft)
    edit(copy)
    setDraft(copy)
  }
  const invalidate = () => {
    setDraft(null)
    setOriginal(null)
    setResult(null)
    setError('')
  }

  async function doParse() {
    invalidate()
    try {
      const response = await parse.mutateAsync()
      setOriginal(structuredClone(response.draft))
      setDraft(structuredClone(response.draft))
      setResult(response)
    } catch (err) {
      setError((err as Error).message)
    }
  }
  async function doSave() {
    setError('')
    try {
      await save.mutateAsync()
      await queryClient.invalidateQueries({ queryKey: meetingsKey })
      onClose()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <Dialog
      open
      onOpenChange={(next) => {
        if (!next && !busy) onClose()
      }}
    >
      <DialogContent className="max-h-[90svh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Paste an agenda — {meeting.title}</DialogTitle>
          <DialogDescription>
            Parse proposes an agenda for this existing meeting. Review before Save. Meeting details
            stay unchanged.
          </DialogDescription>
        </DialogHeader>
        <fieldset disabled={busy} className="grid gap-3">
          <label htmlFor="agenda-text">Agenda text</label>
          <Textarea
            id="agenda-text"
            rows={5}
            maxLength={12000}
            value={text}
            onChange={(e) => {
              setText(e.target.value)
              invalidate()
            }}
          />
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              setText(example)
              invalidate()
            }}
          >
            Use mock agenda example
          </Button>
          <label htmlFor="agenda-zone">Source timezone (IANA)</label>
          <Input
            id="agenda-zone"
            value={timezone}
            onChange={(e) => {
              setTimezone(e.target.value)
              invalidate()
            }}
          />
          <label htmlFor="agenda-reference">
            Reference date for relative deadlines (in source timezone)
          </label>
          <Input
            id="agenda-reference"
            type="date"
            value={referenceDate}
            onChange={(e) => {
              setReferenceDate(e.target.value)
              invalidate()
            }}
          />
          <Button type="button" disabled={!text.trim() || busy} onClick={doParse}>
            {parse.isPending ? 'Parsing…' : 'Parse'}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              setDraft({ summary: '', items: [emptyItem()] })
              setOriginal(null)
              setResult(null)
              setError('')
            }}
          >
            Fill agenda manually
          </Button>
          {draft && (
            <>
              <p role="status">
                {result?.warnings.join(' ') ??
                  (original
                    ? 'Review the saved agenda. Original AI suggestion is preserved.'
                    : 'Manual agenda. No AI suggestion will be recorded.')}
              </p>
              {result && (
                <p className="text-sm">
                  {result.metrics.provider} · {result.metrics.latency_ms} ms · tokens{' '}
                  {result.metrics.input_tokens ?? 'N/A'} / {result.metrics.output_tokens ?? 'N/A'} ·
                  estimated USD {result.metrics.estimated_cost_usd ?? 'N/A'}
                </p>
              )}
              <label htmlFor="agenda-summary">Summary</label>
              <Input
                id="agenda-summary"
                value={draft.summary}
                onChange={(e) =>
                  change((v) => {
                    v.summary = e.target.value
                  })
                }
              />
              {draft.items.map((item, i) => (
                <section key={i} className="grid gap-2 rounded border p-3">
                  <h3>Agenda item {i + 1}</h3>
                  <label>
                    Topic
                    <Input
                      value={item.topic}
                      onChange={(e) =>
                        change((v) => {
                          v.items[i].topic = e.target.value
                        })
                      }
                    />
                  </label>
                  <label>
                    Owner
                    <Input
                      value={item.owner ?? ''}
                      onChange={(e) =>
                        change((v) => {
                          v.items[i].owner = e.target.value || null
                        })
                      }
                    />
                  </label>
                  <label>
                    Duration (minutes)
                    <Input
                      type="number"
                      min={1}
                      max={1440}
                      value={item.duration_minutes ?? ''}
                      onChange={(e) =>
                        change((v) => {
                          v.items[i].duration_minutes = e.target.value
                            ? Number(e.target.value)
                            : null
                        })
                      }
                    />
                  </label>
                  <label>
                    Notes
                    <Textarea
                      value={item.notes}
                      onChange={(e) =>
                        change((v) => {
                          v.items[i].notes = e.target.value
                        })
                      }
                    />
                  </label>
                  {item.action_items.map((action, j) => (
                    <div key={j} className="grid gap-2 border-l pl-3">
                      <label>
                        Action item
                        <Input
                          value={action.task}
                          onChange={(e) =>
                            change((v) => {
                              v.items[i].action_items[j].task = e.target.value
                            })
                          }
                        />
                      </label>
                      <label>
                        Action owner
                        <Input
                          value={action.owner ?? ''}
                          onChange={(e) =>
                            change((v) => {
                              v.items[i].action_items[j].owner = e.target.value || null
                            })
                          }
                        />
                      </label>
                      <label>
                        Deadline
                        <Input
                          type="date"
                          value={action.deadline ?? ''}
                          onChange={(e) =>
                            change((v) => {
                              v.items[i].action_items[j].deadline = e.target.value || null
                            })
                          }
                        />
                      </label>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() =>
                          change((v) => {
                            v.items[i].action_items.splice(j, 1)
                          })
                        }
                      >
                        Remove action
                      </Button>
                    </div>
                  ))}
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() =>
                      change((v) => {
                        v.items[i].action_items.push({ task: '', owner: null, deadline: null })
                      })
                    }
                  >
                    Add action item
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() =>
                      change((v) => {
                        v.items.splice(i, 1)
                      })
                    }
                  >
                    Remove agenda item
                  </Button>
                </section>
              ))}
              <Button
                type="button"
                variant="outline"
                onClick={() =>
                  change((v) => {
                    v.items.push(emptyItem())
                  })
                }
              >
                Add agenda item
              </Button>
              {original && (
                <details>
                  <summary>Original AI suggestion (read only)</summary>
                  <pre className="overflow-auto text-xs">{JSON.stringify(original, null, 2)}</pre>
                </details>
              )}
              <Button type="button" disabled={busy || draft.items.length === 0} onClick={doSave}>
                {save.isPending ? 'Saving…' : 'Save agenda'}
              </Button>
            </>
          )}
        </fieldset>
        {error && (
          <p role="alert" className="text-destructive">
            {error}
          </p>
        )}
      </DialogContent>
    </Dialog>
  )
}
