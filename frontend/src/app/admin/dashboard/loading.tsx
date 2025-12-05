export default function DashboardLoading() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 w-64 bg-gray-200 dark:bg-gray-700 rounded"></div>

      <div className="grid gap-4 md:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="card">
            <div className="h-4 w-24 bg-gray-200 dark:bg-gray-700 rounded mb-3"></div>
            <div className="h-8 w-16 bg-gray-200 dark:bg-gray-700 rounded"></div>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded"></div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="card">
            <div className="h-6 w-32 bg-gray-200 dark:bg-gray-700 rounded mb-3"></div>
            <div className="space-y-2">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
