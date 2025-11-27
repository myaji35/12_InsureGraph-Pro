"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ChevronLeft, FileText, CheckCircle, Circle } from "lucide-react";

interface InsurerDetailViewProps {
  insurer: string;
  onBack: () => void;
}

// 카테고리별 상품 데이터 (예시)
const PRODUCT_CATEGORIES = [
  { id: "life", name: "종신보험", products: [] },
  { id: "term", name: "정기보험", products: [] },
  { id: "annuity", name: "연금보험", products: [] },
  { id: "saving", name: "저축보험", products: [] },
  { id: "ci", name: "CI보험", products: [] },
  { id: "health", name: "건강보험", products: [] },
];

// 메트라이프생명의 학습된 문서
const METLIFE_LEARNED_DOCS = [
  {
    id: "983882c9-8728-4a23-b04c-e4a7557ec8e4",
    name: "무배당 하이라이프종신보험 약관",
    category: "종신보험",
    launchDate: "2025-09-01",
    status: "completed" as const,
  },
];

export default function InsurerDetailView({
  insurer,
  onBack,
}: InsurerDetailViewProps) {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  // 메트라이프생명인 경우 학습된 문서 1개 표시
  const learnedDocs = insurer === "메트라이프생명" ? METLIFE_LEARNED_DOCS : [];

  // 나머지는 미학습 문서로 표시 (실제로는 API에서 가져와야 함)
  const unlearnedDocs = Array.from({ length: 45 }, (_, i) => ({
    id: `unlearned-${i}`,
    name: `상품 약관 ${i + 1}`,
    category: PRODUCT_CATEGORIES[i % PRODUCT_CATEGORIES.length].name,
    launchDate: new Date(2024, Math.floor(i / 8), (i % 28) + 1)
      .toISOString()
      .split("T")[0],
    status: "pending" as const,
  }));

  const allDocs = [...learnedDocs, ...unlearnedDocs].sort(
    (a, b) => new Date(b.launchDate).getTime() - new Date(a.launchDate).getTime()
  );

  const filteredDocs = selectedCategory
    ? allDocs.filter((doc) => doc.category === selectedCategory)
    : allDocs;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={onBack}>
          <ChevronLeft className="h-4 w-4 mr-1" />
          목록으로
        </Button>
        <h2 className="text-2xl font-bold">{insurer}</h2>
      </div>

      {/* 통계 요약 */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">전체 문서</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{allDocs.length}개</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">학습 완료</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {learnedDocs.length}개
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">미학습</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {unlearnedDocs.length}개
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 카테고리 필터 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">상품 카테고리</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            <Button
              variant={selectedCategory === null ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedCategory(null)}
            >
              전체
            </Button>
            {PRODUCT_CATEGORIES.map((category) => (
              <Button
                key={category.id}
                variant={selectedCategory === category.name ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedCategory(category.name)}
              >
                {category.name}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 문서 목록 탭 */}
      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">
            전체 ({filteredDocs.length})
          </TabsTrigger>
          <TabsTrigger value="learned">
            학습 완료 ({learnedDocs.length})
          </TabsTrigger>
          <TabsTrigger value="unlearned">
            미학습 ({unlearnedDocs.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-2">
          {filteredDocs.map((doc) => (
            <DocumentCard key={doc.id} doc={doc} insurer={insurer} />
          ))}
        </TabsContent>

        <TabsContent value="learned" className="space-y-2">
          {learnedDocs
            .filter((doc) =>
              selectedCategory ? doc.category === selectedCategory : true
            )
            .map((doc) => (
              <DocumentCard key={doc.id} doc={doc} insurer={insurer} />
            ))}
        </TabsContent>

        <TabsContent value="unlearned" className="space-y-2">
          {unlearnedDocs
            .filter((doc) =>
              selectedCategory ? doc.category === selectedCategory : true
            )
            .map((doc) => (
              <DocumentCard key={doc.id} doc={doc} insurer={insurer} />
            ))}
        </TabsContent>
      </Tabs>
    </div>
  );
}

interface DocumentCardProps {
  doc: {
    id: string;
    name: string;
    category: string;
    launchDate: string;
    status: "completed" | "pending";
  };
  insurer: string;
}

function DocumentCard({ doc, insurer }: DocumentCardProps) {
  const isLearned = doc.status === "completed";

  return (
    <Card
      className={`cursor-pointer hover:shadow-md transition-shadow ${
        isLearned ? "border-green-200 bg-green-50/30" : "border-orange-200 bg-orange-50/20"
      }`}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1">
            {isLearned ? (
              <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
            ) : (
              <Circle className="h-5 w-5 text-orange-500 mt-0.5" />
            )}
            <div className="flex-1 space-y-1">
              <div className="flex items-center gap-2">
                <h4 className="font-medium">{doc.name}</h4>
                <Badge variant="outline" className="text-xs">
                  {doc.category}
                </Badge>
              </div>
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <span>판매 시점: {doc.launchDate}</span>
                <span>{insurer}</span>
              </div>
            </div>
          </div>
          <Badge
            variant={isLearned ? "default" : "secondary"}
            className={isLearned ? "bg-green-600" : "bg-orange-500"}
          >
            {isLearned ? "학습 완료" : "미학습"}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}
