"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

interface InsurerStatsGridProps {
  insurers: string[];
  onSelectInsurer: (insurer: string) => void;
}

// 보험사별 임시 통계 데이터 (실제로는 API에서 가져와야 함)
const getInsurerStats = (insurer: string) => {
  // 메트라이프생명만 학습 완료 1개
  const isMetlife = insurer === "메트라이프생명";

  return {
    expectedDocs: Math.floor(Math.random() * 30) + 30, // 30-60개
    learnedDocs: isMetlife ? 1 : 0,
    inProgress: Math.floor(Math.random() * 3), // 0-3개
  };
};

export default function InsurerStatsGrid({
  insurers,
  onSelectInsurer,
}: InsurerStatsGridProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {insurers.map((insurer) => {
        const stats = getInsurerStats(insurer);
        const progress = (stats.learnedDocs / stats.expectedDocs) * 100;
        const hasData = stats.learnedDocs > 0;

        return (
          <Card
            key={insurer}
            className="cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => onSelectInsurer(insurer)}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">{insurer}</CardTitle>
                {hasData && (
                  <Badge variant="default" className="bg-green-600">
                    학습 완료
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">예상 문서</span>
                <span className="font-medium">{stats.expectedDocs}개</span>
              </div>

              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">학습 완료</span>
                <span className="font-medium text-green-600">
                  {stats.learnedDocs}개
                </span>
              </div>

              {stats.inProgress > 0 && (
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">처리 중</span>
                  <span className="font-medium text-blue-600">
                    {stats.inProgress}개
                  </span>
                </div>
              )}

              <div className="space-y-1">
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>진행률</span>
                  <span>{progress.toFixed(1)}%</span>
                </div>
                <Progress value={progress} className="h-2" />
              </div>

              <div className="flex justify-between text-sm text-muted-foreground pt-1">
                <span>미학습</span>
                <span className="font-medium text-orange-600">
                  {stats.expectedDocs - stats.learnedDocs - stats.inProgress}개
                </span>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
