import toast, { Toaster } from 'react-hot-toast'

export const showSuccess = (message: string, duration = 4000) => {
  toast.success(message, {
    duration,
    position: 'top-right',
    style: {
      background: '#10b981',
      color: '#fff',
      borderRadius: '8px',
      padding: '16px',
    },
    iconTheme: {
      primary: '#fff',
      secondary: '#10b981',
    },
  })
}

export const showError = (message: string, duration = 5000) => {
  toast.error(message, {
    duration,
    position: 'top-right',
    style: {
      background: '#ef4444',
      color: '#fff',
      borderRadius: '8px',
      padding: '16px',
    },
    iconTheme: {
      primary: '#fff',
      secondary: '#ef4444',
    },
  })
}

export const showInfo = (message: string, duration = 3000) => {
  toast(message, {
    duration,
    position: 'top-right',
    icon: 'ℹ️',
    style: {
      background: '#3b82f6',
      color: '#fff',
      borderRadius: '8px',
      padding: '16px',
    },
  })
}

export const showWarning = (message: string, duration = 4000) => {
  toast(message, {
    duration,
    position: 'top-right',
    icon: '⚠️',
    style: {
      background: '#f59e0b',
      color: '#fff',
      borderRadius: '8px',
      padding: '16px',
    },
  })
}

export const showLoading = (message: string) => {
  return toast.loading(message, {
    position: 'top-right',
    style: {
      borderRadius: '8px',
      padding: '16px',
    },
  })
}

export const dismissToast = (id: string) => {
  toast.dismiss(id)
}

// Promise-based toast for async operations
export const showPromise = <T,>(
  promise: Promise<T>,
  messages: {
    loading: string
    success: string
    error: string
  }
) => {
  return toast.promise(promise, {
    loading: messages.loading,
    success: messages.success,
    error: messages.error,
  })
}

export { Toaster }
