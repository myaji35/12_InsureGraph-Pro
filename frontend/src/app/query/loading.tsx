export default function QueryLoading() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 w-32 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
      <div className="h-4 w-96 bg-gray-200 dark:bg-gray-700 rounded mb-8"></div>

      <div className="card">
        <div className="space-y-4">
          <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
          <div className="h-10 w-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
    </div>
  )
}
