"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { useState, useEffect } from "react";

interface InsurerStatsGridProps {
  insurers: string[];
  onSelectInsurer: (insurer: string) => void;
}

// 보험사 이름 -> 코드 변환 매핑
const INSURER_NAME_TO_CODE: Record<string, string> = {
  "메트라이프생명": "metlife",
  "삼성생명": "samsung_life",
  "삼성화재": "samsung_fire",
  "KB손해보험": "kb_insurance",
  // 필요한 보험사 추가...
};

// 보험사 이름을 코드로 변환
const convertInsurerNameToCode = (name: string): string => {
  return INSURER_NAME_TO_CODE[name] || name.toLowerCase().replace(/\s+/g, '_');
};

// 보험사별 임시 통계 데이터 (실제로는 API에서 가져와야 함)
const getInsurerStats = (insurer: string) => {
  // 메트라이프생명만 학습 완료 1개
  const isMetlife = insurer === "메트라이프생명";

  // 보험사명을 기반으로 일관된 "랜덤" 값 생성 (시드 기반)
  const seed = insurer.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  const pseudoRandom1 = (seed * 9301 + 49297) % 233280 / 233280;
  const pseudoRandom2 = ((seed + 1) * 9301 + 49297) % 233280 / 233280;

  return {
    expectedDocs: Math.floor(pseudoRandom1 * 30) + 30, // 30-60개
    learnedDocs: isMetlife ? 1 : 0,
    inProgress: Math.floor(pseudoRandom2 * 3), // 0-3개
  };
};

export default function InsurerStatsGrid({
  insurers,
  onSelectInsurer,
}: InsurerStatsGridProps) {
  const [mounted, setMounted] = useState(false);
  const [resettingInsurers, setResettingInsurers] = useState<Set<string>>(new Set());

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleResetInsurer = async (insurer: string, e: React.MouseEvent) => {
    e.stopPropagation(); // 카드 클릭 이벤트 방지

    const confirmReset = confirm(
      `${insurer}의 모든 학습 데이터를 초기화하시겠습니까?\n\n` +
      `경고: 학습된 데이터가 모두 삭제되고 처음부터 다시 학습해야 합니다.`
    );

    if (!confirmReset) return;

    setResettingInsurers(prev => new Set(prev).add(insurer));

    try {
      // 보험사 이름을 코드로 변환 (예: "메트라이프생명" -> "metlife")
      const insurerCode = convertInsurerNameToCode(insurer);

      const response = await fetch(
        `http://localhost:8000/api/v1/crawler/reset-by-insurer/${insurerCode}`,
        { method: 'POST' }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      alert(`✅ ${insurer} 초기화 완료!\n\n초기화된 문서: ${result.reset_count}개`);

      // 페이지 새로고침하여 상태 업데이트
      window.location.reload();
    } catch (error) {
      console.error('Failed to reset insurer:', error);
      alert(`❌ ${insurer} 초기화 실패:\n${error}`);
    } finally {
      setResettingInsurers(prev => {
        const next = new Set(prev);
        next.delete(insurer);
        return next;
      });
    }
  };

  // 클라이언트 마운트 전까지는 플레이스홀더 표시
  if (!mounted) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {insurers.map((insurer) => (
          <Card key={insurer} className="cursor-pointer">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">{insurer}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="h-20 animate-pulse bg-gray-100 rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }
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
                <div className="flex items-center gap-2">
                  {hasData && (
                    <>
                      <Badge variant="default" className="bg-green-600">
                        학습 완료
                      </Badge>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => handleResetInsurer(insurer, e)}
                        disabled={resettingInsurers.has(insurer)}
                        className="h-6 px-2 text-xs"
                      >
                        {resettingInsurers.has(insurer) ? '초기화 중...' : '초기화'}
                      </Button>
                    </>
                  )}
                </div>
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
