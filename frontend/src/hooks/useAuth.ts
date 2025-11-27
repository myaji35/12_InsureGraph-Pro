'use client'

import { useUser } from '@clerk/nextjs'

const ADMIN_EMAIL = 'myaji35@gmail.com'

export function useAuth() {
  const { user, isLoaded, isSignedIn } = useUser()

  const isAdmin = isLoaded && isSignedIn && user?.primaryEmailAddress?.emailAddress === ADMIN_EMAIL

  return {
    user,
    isLoaded,
    isSignedIn,
    isAdmin,
    email: user?.primaryEmailAddress?.emailAddress,
  }
}
