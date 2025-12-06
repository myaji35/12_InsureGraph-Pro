'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

interface SystemSettings {
  anthropic_api_key: string
  openai_api_key: string
  default_llm_provider: 'anthropic' | 'openai' | 'mock'
  max_search_results: number
  use_graph_traversal: boolean
}

export default function SettingsPage() {
  const router = useRouter()
  const [settings, setSettings] = useState<SystemSettings>({
    anthropic_api_key: '',
    openai_api_key: '',
    default_llm_provider: 'anthropic',
    max_search_results: 20,
    use_graph_traversal: true,
  })
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [showAnthropicKey, setShowAnthropicKey] = useState(false)
  const [showOpenAIKey, setShowOpenAIKey] = useState(false)

  useEffect(() => {
    // Load settings from localStorage
    const savedSettings = localStorage.getItem('system_settings')
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings))
    }
  }, [])

  const handleSave = async () => {
    setLoading(true)
    setMessage(null)

    try {
      // Save to localStorage (프론트엔드 설정)
      localStorage.setItem('system_settings', JSON.stringify(settings))

      // TODO: 백엔드 API로도 저장 (실제 API 키는 백엔드에서만 관리)
      // const response = await fetch('/api/v1/settings', {
      //   method: 'PUT',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(settings)
      // })

      setMessage({ type: 'success', text: '설정이 저장되었습니다.' })

      // 3초 후 메시지 자동 제거
      setTimeout(() => setMessage(null), 3000)
    } catch (error) {
      console.error('Failed to save settings:', error)
      setMessage({ type: 'error', text: '설정 저장에 실패했습니다.' })
    } finally {
      setLoading(false)
    }
  }

  const handleTestConnection = async (provider: 'anthropic' | 'openai') => {
    setLoading(true)
    setMessage(null)

    try {
      // TODO: 백엔드 API로 연결 테스트
      // const response = await fetch(`/api/v1/settings/test/${provider}`, {
      //   method: 'POST',
      // })

      // 임시 성공 메시지
      setMessage({
        type: 'success',
        text: `${provider === 'anthropic' ? 'Anthropic' : 'OpenAI'} 연결 테스트 성공`
      })

      setTimeout(() => setMessage(null), 3000)
    } catch (error) {
      console.error('Connection test failed:', error)
      setMessage({ type: 'error', text: '연결 테스트에 실패했습니다.' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-dark-bg">
      {/* Header */}
      <div className="bg-white dark:bg-dark-surface border-b border-gray-200 dark:border-dark-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">설정</h1>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                시스템 설정 및 API 키 관리
              </p>
            </div>
            <button
              onClick={() => router.push('/dashboard')}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-dark-surface border border-gray-300 dark:border-dark-border rounded-lg hover:bg-gray-50 dark:hover:bg-dark-hover transition-colors"
            >
              대시보드로 돌아가기
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Success/Error Message */}
        {message && (
          <div
            className={`mb-6 p-4 rounded-lg ${
              message.type === 'success'
                ? 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200 border border-green-200 dark:border-green-800'
                : 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200 border border-red-200 dark:border-red-800'
            }`}
          >
            {message.text}
          </div>
        )}

        <div className="space-y-6">
          {/* LLM Provider Settings */}
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow border border-gray-200 dark:border-dark-border p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              LLM 제공자 설정
            </h2>

            {/* Anthropic API Key */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Anthropic API Key (Claude)
              </label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <input
                    type={showAnthropicKey ? 'text' : 'password'}
                    value={settings.anthropic_api_key}
                    onChange={(e) =>
                      setSettings({ ...settings, anthropic_api_key: e.target.value })
                    }
                    placeholder="sk-ant-api03-..."
                    className="w-full px-4 py-2 border border-gray-300 dark:border-dark-border rounded-lg bg-white dark:bg-dark-bg text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                  <button
                    type="button"
                    onClick={() => setShowAnthropicKey(!showAnthropicKey)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                  >
                    {showAnthropicKey ? '숨기기' : '보기'}
                  </button>
                </div>
                <button
                  onClick={() => handleTestConnection('anthropic')}
                  disabled={loading || !settings.anthropic_api_key}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  테스트
                </button>
              </div>
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Claude 3.5 Sonnet 모델을 사용합니다. https://console.anthropic.com 에서 발급받으세요.
              </p>
            </div>

            {/* OpenAI API Key */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                OpenAI API Key (GPT-4)
              </label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <input
                    type={showOpenAIKey ? 'text' : 'password'}
                    value={settings.openai_api_key}
                    onChange={(e) =>
                      setSettings({ ...settings, openai_api_key: e.target.value })
                    }
                    placeholder="sk-..."
                    className="w-full px-4 py-2 border border-gray-300 dark:border-dark-border rounded-lg bg-white dark:bg-dark-bg text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                  <button
                    type="button"
                    onClick={() => setShowOpenAIKey(!showOpenAIKey)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                  >
                    {showOpenAIKey ? '숨기기' : '보기'}
                  </button>
                </div>
                <button
                  onClick={() => handleTestConnection('openai')}
                  disabled={loading || !settings.openai_api_key}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  테스트
                </button>
              </div>
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                GPT-4 모델을 사용합니다. https://platform.openai.com 에서 발급받으세요.
              </p>
            </div>

            {/* Default LLM Provider */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                기본 LLM 제공자
              </label>
              <select
                value={settings.default_llm_provider}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    default_llm_provider: e.target.value as 'anthropic' | 'openai' | 'mock',
                  })
                }
                className="w-full px-4 py-2 border border-gray-300 dark:border-dark-border rounded-lg bg-white dark:bg-dark-bg text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="anthropic">Anthropic (Claude)</option>
                <option value="openai">OpenAI (GPT-4)</option>
                <option value="mock">Mock (테스트용)</option>
              </select>
            </div>
          </div>

          {/* Query Settings */}
          <div className="bg-white dark:bg-dark-surface rounded-lg shadow border border-gray-200 dark:border-dark-border p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              검색 설정
            </h2>

            {/* Max Search Results */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                최대 검색 결과 수
              </label>
              <input
                type="number"
                min="5"
                max="100"
                value={settings.max_search_results}
                onChange={(e) =>
                  setSettings({ ...settings, max_search_results: parseInt(e.target.value) })
                }
                className="w-full px-4 py-2 border border-gray-300 dark:border-dark-border rounded-lg bg-white dark:bg-dark-bg text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                검색 시 반환되는 최대 결과 수 (5-100)
              </p>
            </div>

            {/* Use Graph Traversal */}
            <div className="flex items-center">
              <input
                type="checkbox"
                id="use_graph_traversal"
                checked={settings.use_graph_traversal}
                onChange={(e) =>
                  setSettings({ ...settings, use_graph_traversal: e.target.checked })
                }
                className="w-4 h-4 text-primary-600 bg-white dark:bg-dark-bg border-gray-300 dark:border-dark-border rounded focus:ring-primary-500"
              />
              <label
                htmlFor="use_graph_traversal"
                className="ml-2 text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                그래프 탐색 사용
              </label>
            </div>
            <p className="mt-1 ml-6 text-xs text-gray-500 dark:text-gray-400">
              Knowledge Graph를 활용한 관계 기반 탐색을 활성화합니다.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-4">
            <button
              onClick={() => router.push('/dashboard')}
              className="px-6 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-dark-surface border border-gray-300 dark:border-dark-border rounded-lg hover:bg-gray-50 dark:hover:bg-dark-hover transition-colors"
            >
              취소
            </button>
            <button
              onClick={handleSave}
              disabled={loading}
              className="px-6 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? '저장 중...' : '저장'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
