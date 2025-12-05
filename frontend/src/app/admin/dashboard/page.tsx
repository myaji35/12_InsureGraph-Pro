"use client";

import { useState } from "react";
import Link from "next/link";
import DashboardLayout from "@/components/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import InsurerStatsGrid from "@/components/dashboard/InsurerStatsGrid";
import InsurerDetailView from "@/components/dashboard/InsurerDetailView";
import TimeSeriesChart from "@/components/dashboard/TimeSeriesChart";
import CrawlingProgressMonitor from "@/components/dashboard/CrawlingProgressMonitor";
import DocumentProcessingViewer from "@/components/dashboard/DocumentProcessingViewer";
import GraphRAGLearningProgress from "@/components/dashboard/GraphRAGLearningProgress";

// 30개 보험사 목록
const INSURERS = [
  "삼성생명", "한화생명", "교보생명", "DB생명", "신한라이프",
  "메트라이프생명", "처브라이프", "푸르덴셜생명", "AIA생명", "DGB생명",
  "ABL생명", "KB라이프생명", "BNP파리바카디프생명", "KDB생명", "IBK연금보험",
  "삼성화재", "현대해상", "DB손해보험", "KB손해보험", "메리츠화재",
  "한화손해보험", "롯데손해보험", "MG손해보험", "흥국화재", "캐롯손해보험",
  "AXA손해보험", "하나손해보험", "NH농협손해보험", "BNK손해보험", "THE K손해보험"
];

export default function DashboardPage() {
  const [selectedInsurer, setSelectedInsurer] = useState<string | null>(null);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">보험사별 문서 학습 현황</h1>
            <p className="text-muted-foreground mt-2">
              30개 보험사의 문서 학습 진행 상황을 한눈에 확인하세요
            </p>
          </div>
          <Link href="/admin/metadata">
            <Button size="lg" className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700">
              📋 정책 메타데이터 관리
            </Button>
          </Link>
        </div>

        {/* 전체 통계 요약 */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">총 보험사</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">30개</div>
              <p className="text-xs text-muted-foreground">
                생명보험 15개, 손해보험 15개
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">예상 문서 수</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">1,200개</div>
              <p className="text-xs text-muted-foreground">
                평균 40개/보험사
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">학습 완료</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">1개</div>
              <p className="text-xs text-muted-foreground">
                전체의 0.08%
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">미학습</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600">1,199개</div>
              <p className="text-xs text-muted-foreground">
                학습 대기 중
              </p>
            </CardContent>
          </Card>
        </div>

        {/* GraphRAG 학습 진행 상황 */}
        <GraphRAGLearningProgress />

        {/* 실시간 크롤링 진행 상황 */}
        <CrawlingProgressMonitor />

        {/* 문서 학습 실시간 뷰어 */}
        <DocumentProcessingViewer autoSelectLatest={true} />

        {/* 시계열 그래프 */}
        <Card>
          <CardHeader>
            <CardTitle>학습 문서 추이</CardTitle>
          </CardHeader>
          <CardContent>
            <TimeSeriesChart />
          </CardContent>
        </Card>

        {/* 보험사 목록 또는 상세보기 */}
        {selectedInsurer ? (
          <InsurerDetailView
            insurer={selectedInsurer}
            onBack={() => setSelectedInsurer(null)}
          />
        ) : (
          <InsurerStatsGrid
            insurers={INSURERS}
            onSelectInsurer={setSelectedInsurer}
          />
        )}
      </div>
    </DashboardLayout>
  );
}
