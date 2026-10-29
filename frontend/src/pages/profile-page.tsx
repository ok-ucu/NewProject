import { useState, type FormEvent } from 'react'
import { ArrowLeftIcon, LogOutIcon } from 'lucide-react'
import { Link } from 'react-router'

import { PasswordInput } from '@/components/auth-layout'
import { Button } from '@/components/ui/button'
import { Field, FieldGroup, FieldLabel } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import {
  useChangeEmail,
  useChangePassword,
  useConfirmEmail,
  useResendEmailCode,
  useUpdateName,
  useAuth,
} from '@/lib/auth'

export function ProfilePage() {
  const { user, signOut } = useAuth()
  const [name, setName] = useState(user?.name ?? '')
  const [email, setEmail] = useState('')
  const [emailCode, setEmailCode] = useState('')
  const [verifyingEmail, setVerifyingEmail] = useState(false)
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const updateName = useUpdateName()
  const changeEmail = useChangeEmail()
  const confirmEmail = useConfirmEmail()
  const resendEmailCode = useResendEmailCode()
  const changePassword = useChangePassword()

  const run = (action: () => void) => {
    setMessage('')
    setError('')
    action()
  }

  const saveName = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    run(() =>
      updateName.mutate(name.trim(), {
        onSuccess: () => setMessage('Name updated.'),
        onError: (cause) => setError(cause.message),
      }),
    )
  }

  const saveEmail = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (verifyingEmail) {
      run(() =>
        confirmEmail.mutate(emailCode, {
          onSuccess: () => {
            setEmail('')
            setEmailCode('')
            setVerifyingEmail(false)
            setMessage('Email updated.')
          },
          onError: (cause) => setError(cause.message),
        }),
      )
      return
    }
    run(() =>
      changeEmail.mutate(email.trim(), {
        onSuccess: ({ needsConfirmation }) => {
          if (needsConfirmation) setVerifyingEmail(true)
          else setMessage('Email updated.')
        },
        onError: (cause) => setError(cause.message),
      }),
    )
  }

  const savePassword = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.')
      setMessage('')
      return
    }
    run(() =>
      changePassword.mutate(
        { currentPassword, newPassword },
        {
          onSuccess: () => {
            setCurrentPassword('')
            setNewPassword('')
            setConfirmPassword('')
            setMessage('Password updated.')
          },
          onError: (cause) => setError(cause.message),
        },
      ),
    )
  }

  return (
    <main className="mx-auto flex min-h-svh w-full max-w-2xl flex-col gap-6 px-4 py-6 sm:px-6">
      <header className="flex items-center gap-3">
        <Button asChild variant="ghost" size="icon-sm" aria-label="Back to meetings">
          <Link to="/home">
            <ArrowLeftIcon />
          </Link>
        </Button>
        <div>
          <p className="text-xs font-semibold tracking-[0.2em] text-muted-foreground uppercase">
            Meetings
          </p>
          <h1 className="text-3xl">Profile</h1>
        </div>
      </header>

      <section className="flex items-center gap-4 rounded-[20px] bg-card p-5">
        <div className="flex size-12 shrink-0 items-center justify-center rounded-full bg-secondary text-xl font-semibold text-secondary-foreground">
          {user?.name.charAt(0).toUpperCase()}
        </div>
        <div className="min-w-0">
          <p className="truncate font-semibold">{user?.name}</p>
          <p className="truncate text-sm text-muted-foreground">{user?.email}</p>
        </div>
      </section>

      {message && (
        <p role="status" className="text-sm text-muted-foreground">
          {message}
        </p>
      )}
      {error && (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}

      {user?.provider === 'google' ? (
        <section className="rounded-[20px] bg-card p-5">
          <h2 className="text-xl">Account details</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Your name, email, and password are managed by Google.
          </p>
        </section>
      ) : (
        <>
          <section className="rounded-[20px] bg-card p-5">
            <h2 className="mb-4 text-xl">Name</h2>
            <form onSubmit={saveName}>
              <FieldGroup>
                <Field>
                  <FieldLabel htmlFor="profile-name">Name</FieldLabel>
                  <Input
                    id="profile-name"
                    autoComplete="name"
                    required
                    maxLength={100}
                    value={name}
                    onChange={(event) => setName(event.target.value)}
                  />
                </Field>
                <Button type="submit" disabled={updateName.isPending || name.trim() === user?.name}>
                  {updateName.isPending ? 'Saving...' : 'Save name'}
                </Button>
              </FieldGroup>
            </form>
          </section>

          <section className="rounded-[20px] bg-card p-5">
            <h2 className="mb-4 text-xl">Email</h2>
            <form onSubmit={saveEmail}>
              <FieldGroup>
                {verifyingEmail ? (
                  <>
                    <p className="text-sm text-muted-foreground">
                      Enter the verification code sent to {email}.
                    </p>
                    <Field>
                      <FieldLabel htmlFor="profile-email-code">Verification code</FieldLabel>
                      <Input
                        id="profile-email-code"
                        autoComplete="one-time-code"
                        required
                        value={emailCode}
                        onChange={(event) => setEmailCode(event.target.value)}
                      />
                    </Field>
                    <div className="flex flex-wrap gap-2">
                      <Button type="submit" disabled={confirmEmail.isPending}>
                        {confirmEmail.isPending ? 'Verifying...' : 'Verify email'}
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        disabled={resendEmailCode.isPending}
                        onClick={() =>
                          run(() =>
                            resendEmailCode.mutate(undefined, {
                              onSuccess: () => setMessage('A new code was sent.'),
                              onError: (cause) => setError(cause.message),
                            }),
                          )
                        }
                      >
                        Send a new code
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        onClick={() => {
                          setVerifyingEmail(false)
                          setEmailCode('')
                        }}
                      >
                        Cancel
                      </Button>
                    </div>
                  </>
                ) : (
                  <>
                    <Field>
                      <FieldLabel htmlFor="profile-email">New email</FieldLabel>
                      <Input
                        id="profile-email"
                        type="email"
                        autoComplete="email"
                        required
                        value={email}
                        onChange={(event) => setEmail(event.target.value)}
                      />
                    </Field>
                    <Button type="submit" disabled={changeEmail.isPending || !email.trim()}>
                      {changeEmail.isPending ? 'Sending code...' : 'Change email'}
                    </Button>
                  </>
                )}
              </FieldGroup>
            </form>
          </section>

          <section className="rounded-[20px] bg-card p-5">
            <h2 className="mb-4 text-xl">Password</h2>
            <form onSubmit={savePassword}>
              <FieldGroup>
                <Field>
                  <FieldLabel htmlFor="profile-current-password">Current password</FieldLabel>
                  <PasswordInput
                    id="profile-current-password"
                    autoComplete="current-password"
                    required
                    value={currentPassword}
                    onChange={(event) => setCurrentPassword(event.target.value)}
                  />
                </Field>
                <Field>
                  <FieldLabel htmlFor="profile-new-password">New password</FieldLabel>
                  <PasswordInput
                    id="profile-new-password"
                    autoComplete="new-password"
                    minLength={8}
                    required
                    value={newPassword}
                    onChange={(event) => setNewPassword(event.target.value)}
                  />
                </Field>
                <Field>
                  <FieldLabel htmlFor="profile-confirm-password">Confirm new password</FieldLabel>
                  <PasswordInput
                    id="profile-confirm-password"
                    autoComplete="new-password"
                    minLength={8}
                    required
                    value={confirmPassword}
                    onChange={(event) => setConfirmPassword(event.target.value)}
                  />
                </Field>
                <Button type="submit" disabled={changePassword.isPending}>
                  {changePassword.isPending ? 'Saving...' : 'Change password'}
                </Button>
              </FieldGroup>
            </form>
          </section>
        </>
      )}

      <Button variant="outline" className="self-start" onClick={signOut}>
        <LogOutIcon />
        Sign out
      </Button>
    </main>
  )
}
