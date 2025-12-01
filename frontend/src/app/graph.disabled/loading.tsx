export default function GraphLoading() {
  return (
    <div className="h-[calc(100vh-120px)] flex flex-col">
      <div className="animate-pulse">
        <div className="flex items-center justify-between mb-3">
          <div>
            <div className="h-8 w-32 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
            <div className="h-4 w-96 bg-gray-200 dark:bg-gray-700 rounded"></div>
          </div>
          <div className="h-10 w-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>

        <div className="flex-1 flex gap-2 overflow-hidden">
          <div className="w-72 h-full bg-gray-200 dark:bg-gray-700 rounded"></div>
          <div className="flex-1 h-96 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
    </div>
  )
}
