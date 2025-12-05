"use client";

import { Card } from "@/components/ui/card";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export default function TimeSeriesChart() {
  // 실제 시계열 데이터 가져오기
  const { data: timeseriesData, isLoading, isError } = useQuery({
    queryKey: ['timeseries-stats'],
    queryFn: () => apiClient.getTimeseriesStats(),
    refetchInterval: 60000, // 1분마다 새로고침
  });

  // 로딩 중일 때
  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-[300px] flex items-center justify-center">
          <p className="text-muted-foreground">데이터를 불러오는 중...</p>
        </div>
        <div className="h-[200px] flex items-center justify-center">
          <p className="text-muted-foreground">데이터를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  // 에러가 발생했을 때
  if (isError || !timeseriesData) {
    return (
      <div className="space-y-4">
        <div className="h-[300px] flex items-center justify-center">
          <p className="text-red-600">데이터를 불러올 수 없습니다.</p>
        </div>
        <div className="h-[200px] flex items-center justify-center">
          <p className="text-red-600">데이터를 불러올 수 없습니다.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 누적 차트 */}
      <div className="h-[300px]">
        <h3 className="text-sm font-medium mb-2">전체 문서 현황 (누적)</h3>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={timeseriesData}>
            <defs>
              <linearGradient id="colorPending" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorLearned" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#16a34a" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#16a34a" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorInProgress" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="date"
              className="text-xs"
              tick={{ fill: "hsl(var(--muted-foreground))" }}
            />
            <YAxis
              className="text-xs"
              tick={{ fill: "hsl(var(--muted-foreground))" }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--background))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "var(--radius)",
              }}
            />
            <Legend />
            <Area
              type="monotone"
              dataKey="pendingDocs"
              stroke="#f59e0b"
              fillOpacity={1}
              fill="url(#colorPending)"
              name="미처리"
              strokeWidth={2}
            />
            <Area
              type="monotone"
              dataKey="learnedDocs"
              stroke="#16a34a"
              fillOpacity={1}
              fill="url(#colorLearned)"
              name="학습 완료"
              stackId="1"
              strokeWidth={2}
            />
            <Area
              type="monotone"
              dataKey="inProgressDocs"
              stroke="#3b82f6"
              fillOpacity={1}
              fill="url(#colorInProgress)"
              name="처리 중"
              stackId="1"
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* 추세선 차트 */}
      <div className="h-[200px]">
        <h3 className="text-sm font-medium mb-2">학습 진행 추세</h3>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={timeseriesData}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="date"
              className="text-xs"
              tick={{ fill: "hsl(var(--muted-foreground))" }}
            />
            <YAxis
              className="text-xs"
              tick={{ fill: "hsl(var(--muted-foreground))" }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--background))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "var(--radius)",
              }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="learnedDocs"
              stroke="#16a34a"
              strokeWidth={3}
              dot={{ fill: "#16a34a", r: 4 }}
              name="학습 완료"
            />
            <Line
              type="monotone"
              dataKey="inProgressDocs"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ fill: "#3b82f6", r: 3 }}
              strokeDasharray="5 5"
              name="처리 중"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
