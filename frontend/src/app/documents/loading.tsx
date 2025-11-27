export default function DocumentsLoading() {
  return (
    <div className="animate-pulse">
      <div className="mb-8">
        <div className="h-8 w-48 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
        <div className="h-4 w-96 bg-gray-200 dark:bg-gray-700 rounded"></div>
      </div>

      <div className="card mb-6">
        <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded"></div>
      </div>

      <div className="card mb-6">
        <div className="flex gap-4">
          <div className="flex-1 h-10 bg-gray-200 dark:bg-gray-700 rounded"></div>
          <div className="w-40 h-10 bg-gray-200 dark:bg-gray-700 rounded"></div>
          <div className="w-40 h-10 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>

      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="card">
            <div className="flex gap-4">
              <div className="w-12 h-12 bg-gray-200 dark:bg-gray-700 rounded"></div>
              <div className="flex-1 space-y-2">
                <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
