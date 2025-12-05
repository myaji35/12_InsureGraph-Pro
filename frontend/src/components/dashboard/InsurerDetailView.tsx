"use client";

import { useState, useMemo, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ChevronLeft, FileText, CheckCircle, Circle, Settings, RefreshCw, Loader2, ExternalLink, X, ChevronDown } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import CrawlerUrlManagementModal from "./CrawlerUrlManagementModal";
import { showSuccess, showError, showInfo } from "@/lib/toast-config";
import { apiClient } from "@/lib/api-client";
import { Progress } from "@/components/ui/progress";

interface InsurerDetailViewProps {
  insurer: string;
  onBack: () => void;
}

type CrawlStep = 'idle' | 'fetching_urls' | 'crawling' | 'analyzing' | 'saving' | 'completed';

export default function InsurerDetailView({
  insurer,
  onBack,
}: InsurerDetailViewProps) {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [isUrlManagementOpen, setIsUrlManagementOpen] = useState(false);
  const [isCrawling, setIsCrawling] = useState(false);
  const [crawlStep, setCrawlStep] = useState<CrawlStep>('idle');
  const [crawlProgress, setCrawlProgress] = useState(0);
  const [crawlMessage, setCrawlMessage] = useState('');
  const [showCrawlConfirm, setShowCrawlConfirm] = useState(false);
  const [crawlerUrls, setCrawlerUrls] = useState<Array<{
    id: string;
    url: string;
    description: string;
  }>>([]);

  // 실제 크롤러 문서 데이터 로드
  const { data: documentsData, isLoading, refetch } = useQuery({
    queryKey: ['crawler-documents', insurer],
    queryFn: () => apiClient.getCrawlerDocuments({ insurer, limit: 1000 }),
    refetchOnWindowFocus: false,
  });

  // 문서를 학습 상태별로 분류
  const { learnedDocs, unlearnedDocs, allDocs } = useMemo(() => {
    if (!documentsData?.items) {
      return { learnedDocs: [], unlearnedDocs: [], allDocs: [] };
    }

    // 제목에서 날짜 추출 (YYYYMMDD 형식)
    const extractDateFromTitle = (title: string): string => {
      // 날짜 패턴 찾기: YYYYMMDD 형식 (예: 20170101, 20190701)
      const dateMatch = title.match(/(\d{8})/);
      if (dateMatch) {
        const dateStr = dateMatch[1];
        const year = dateStr.substring(0, 4);
        const month = dateStr.substring(4, 6);
        const day = dateStr.substring(6, 8);
        return `${year}-${month}-${day}`;
      }
      return '날짜 미상'; // 날짜를 찾을 수 없는 경우
    };

    const docs = documentsData.items.map((doc) => ({
      id: doc.id,
      name: doc.title,
      category: doc.product_type || "기타",
      launchDate: extractDateFromTitle(doc.title),
      // Map backend status properly: processed/completed -> completed, processing -> processing, others -> pending
      status: (doc.status === "processed" || doc.status === "completed") ? "completed" as const :
              doc.status === "processing" ? "processing" as const :
              "pending" as const,
      processingStep: doc.processing_step || null,
      processingProgress: doc.processing_progress || 0,
      processingDetail: doc.processing_detail || null,
      pdfUrl: doc.pdf_url,
    }));

    const learned = docs.filter((doc) => doc.status === "completed");
    const unlearned = docs.filter((doc) => doc.status === "pending" || doc.status === "processing");

    // 미학습 우선 정렬: 미학습(pending/processing) → 학습완료(completed)
    // 각 그룹 내에서는 최신순 정렬
    const sorted = [...docs].sort((a, b) => {
      // 1. 상태별 우선순위: pending/processing(0) < completed(1)
      const statusPriority = (status: string) => status === "completed" ? 1 : 0;
      const statusDiff = statusPriority(a.status) - statusPriority(b.status);

      if (statusDiff !== 0) return statusDiff;

      // 2. 같은 상태 내에서는 날짜순 (최신순)
      if (a.launchDate === '날짜 미상' && b.launchDate === '날짜 미상') return 0;
      if (a.launchDate === '날짜 미상') return 1;
      if (b.launchDate === '날짜 미상') return -1;
      return new Date(b.launchDate).getTime() - new Date(a.launchDate).getTime();
    });

    return {
      learnedDocs: learned,
      unlearnedDocs: unlearned,
      allDocs: sorted
    };
  }, [documentsData]);

  // 카테고리별 필터링
  const filteredDocs = useMemo(() => {
    return selectedCategory
      ? allDocs.filter((doc) => doc.category === selectedCategory)
      : allDocs;
  }, [allDocs, selectedCategory]);

  // 사용 가능한 카테고리 목록 추출
  const availableCategories = useMemo(() => {
    const categories = new Set(allDocs.map((doc) => doc.category));
    return Array.from(categories).sort();
  }, [allDocs]);

  // 처리 중인 문서가 있으면 자동으로 상태를 갱신
  useEffect(() => {
    // 처리 중인 문서가 있는지 확인
    const hasProcessingDocs = allDocs.some(doc => doc.status === "processing");

    if (hasProcessingDocs) {
      // 5초마다 자동으로 새로고침
      const intervalId = setInterval(() => {
        refetch();
      }, 5000);

      return () => clearInterval(intervalId);
    }
  }, [allDocs, refetch]);

  const handleShowCrawlUrls = async () => {
    try {
      // 크롤러 URL 목록 가져오기
      const urls = await apiClient.getCrawlerUrls({ insurer });

      if (urls.length === 0) {
        showError("등록된 크롤링 URL이 없습니다. 먼저 크롤링 설정에서 URL을 추가해주세요.");
        return;
      }

      setCrawlerUrls(urls.map(url => ({
        id: url.id,
        url: url.url,
        description: url.description
      })));
      setShowCrawlConfirm(true);
    } catch (error: any) {
      console.error("Failed to fetch crawler URLs:", error);
      showError("크롤링 URL 목록을 가져오지 못했습니다");
    }
  };

  const handleUpdateDocuments = async () => {
    try {
      setShowCrawlConfirm(false);
      setIsCrawling(true);
      setCrawlStep('fetching_urls');
      setCrawlProgress(10);
      setCrawlMessage('크롤링 URL 목록을 가져오는 중...');
      showInfo("문서 크롤링을 시작합니다...");

      // 단계 1: URL 가져오기 시뮬레이션
      await new Promise(resolve => setTimeout(resolve, 500));

      setCrawlStep('crawling');
      setCrawlProgress(30);
      setCrawlMessage('웹사이트를 크롤링하는 중...');

      const apiBaseUrl =
        process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";

      // 실제 크롤링 시작
      const response = await fetch(
        `${apiBaseUrl}/v1/crawler/crawl-documents?insurer=${encodeURIComponent(insurer)}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "크롤링 실패");
      }

      // 단계 3: AI 분석 중
      setCrawlStep('analyzing');
      setCrawlProgress(60);
      setCrawlMessage('AI로 PDF 문서를 분석하는 중...');

      const result = await response.json();

      // 단계 4: 저장 중
      setCrawlStep('saving');
      setCrawlProgress(85);
      setCrawlMessage('문서를 데이터베이스에 저장하는 중...');
      await new Promise(resolve => setTimeout(resolve, 500));

      // 단계 5: 완료
      setCrawlStep('completed');
      setCrawlProgress(100);
      setCrawlMessage(`총 ${result.total_documents || 0}개 문서 발견!`);

      showSuccess(
        `문서 크롤링 완료: ${result.total_documents || 0}개 문서 발견`
      );

      // 문서 목록 새로고침
      await refetch();

      // 2초 후 상태 초기화
      setTimeout(() => {
        setCrawlStep('idle');
        setCrawlProgress(0);
        setCrawlMessage('');
      }, 2000);
    } catch (error: any) {
      console.error("Failed to crawl documents:", error);
      showError(error.message || "문서 크롤링에 실패했습니다");
      setCrawlStep('idle');
      setCrawlProgress(0);
      setCrawlMessage('');
    } finally {
      setIsCrawling(false);
    }
  };

  // 로딩 중 표시
  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={onBack}>
            <ChevronLeft className="h-4 w-4 mr-1" />
            목록으로
          </Button>
          <h2 className="text-2xl font-bold">{insurer}</h2>
        </div>
        <div className="h-64 flex items-center justify-center">
          <p className="text-muted-foreground">문서 목록을 불러오는 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={onBack}>
          <ChevronLeft className="h-4 w-4 mr-1" />
          목록으로
        </Button>
        <h2 className="text-2xl font-bold">{insurer}</h2>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsUrlManagementOpen(true)}
          className="ml-2"
        >
          <Settings className="h-4 w-4 mr-1" />
          크롤링 설정
        </Button>
        <Button
          variant="default"
          size="sm"
          onClick={handleShowCrawlUrls}
          disabled={isCrawling}
          className="bg-blue-600 hover:bg-blue-700"
        >
          <RefreshCw className={`h-4 w-4 mr-1 ${isCrawling ? "animate-spin" : ""}`} />
          {isCrawling ? "크롤링 중..." : "문서 업데이트"}
        </Button>
      </div>

      {/* URL 관리 모달 */}
      <CrawlerUrlManagementModal
        isOpen={isUrlManagementOpen}
        onClose={() => setIsUrlManagementOpen(false)}
        insurer={insurer}
      />

      {/* 크롤링 확인 다이얼로그 */}
      {showCrawlConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="max-w-2xl w-full mx-4 max-h-[80vh] flex flex-col">
            <CardHeader className="border-b">
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle>크롤링할 URL 목록</CardTitle>
                  <p className="text-sm text-muted-foreground mt-2">
                    다음 URL들에서 문서를 크롤링합니다. 계속하시겠습니까?
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowCrawlConfirm(false)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto p-6">
              <div className="space-y-2">
                {crawlerUrls.map((url) => (
                  <Card key={url.id} className="p-3">
                    <div className="flex items-start gap-2">
                      <ExternalLink className="h-4 w-4 mt-1 text-blue-600 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-700 mb-1">
                          {url.description}
                        </p>
                        <p className="text-xs text-gray-500 break-all">
                          {url.url}
                        </p>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </CardContent>
            <div className="border-t p-4 flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => setShowCrawlConfirm(false)}
              >
                취소
              </Button>
              <Button
                onClick={handleUpdateDocuments}
                className="bg-blue-600 hover:bg-blue-700"
              >
                크롤링 시작
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* 크롤링 진행 상황 */}
      {crawlStep !== 'idle' && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-blue-900">{crawlMessage}</p>
                  <p className="text-xs text-blue-600 mt-1">
                    {crawlStep === 'fetching_urls' && '1/4 단계: URL 목록 가져오는 중'}
                    {crawlStep === 'crawling' && '2/4 단계: 웹사이트 크롤링 중'}
                    {crawlStep === 'analyzing' && '3/4 단계: AI 분석 중'}
                    {crawlStep === 'saving' && '4/4 단계: 저장 중'}
                    {crawlStep === 'completed' && '완료!'}
                  </p>
                </div>
                <span className="text-sm font-semibold text-blue-700">{crawlProgress}%</span>
              </div>
              <Progress value={crawlProgress} className="h-2" />
            </div>
          </CardContent>
        </Card>
      )}

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
      {availableCategories.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">상품약관 및 특약</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              <Button
                variant={selectedCategory === null ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedCategory(null)}
              >
                전체 ({allDocs.length})
              </Button>
              {availableCategories.map((category) => {
                const count = allDocs.filter(doc => doc.category === category).length;
                return (
                  <Button
                    key={category}
                    variant={selectedCategory === category ? "default" : "outline"}
                    size="sm"
                    onClick={() => setSelectedCategory(category)}
                  >
                    {category} ({count})
                  </Button>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

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
            <DocumentCard key={doc.id} doc={doc} insurer={insurer} onRefresh={refetch} />
          ))}
        </TabsContent>

        <TabsContent value="learned" className="space-y-2">
          {learnedDocs
            .filter((doc) =>
              selectedCategory ? doc.category === selectedCategory : true
            )
            .map((doc) => (
              <DocumentCard key={doc.id} doc={doc} insurer={insurer} onRefresh={refetch} />
            ))}
        </TabsContent>

        <TabsContent value="unlearned" className="space-y-2">
          {unlearnedDocs
            .filter((doc) =>
              selectedCategory ? doc.category === selectedCategory : true
            )
            .map((doc) => (
              <DocumentCard key={doc.id} doc={doc} insurer={insurer} onRefresh={refetch} />
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
    status: "completed" | "pending" | "processing";
    processingStep?: string | null;
    processingProgress?: number;
    processingDetail?: any | null;
    pdfUrl?: string;
  };
  insurer: string;
  onRefresh?: () => void;
}

function DocumentCard({ doc, insurer, onRefresh }: DocumentCardProps) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [isDetailExpanded, setIsDetailExpanded] = useState(false);
  const [showLearnModal, setShowLearnModal] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const isLearned = doc.status === "completed";
  const isBeingProcessed = doc.status === "processing" || isProcessing;

  // 서버 상태가 completed나 pending으로 바뀌면 로컬 isProcessing 상태를 초기화
  useEffect(() => {
    if (doc.status === "completed" || doc.status === "pending") {
      setIsProcessing(false);
    }
  }, [doc.status]);

  // 진행 단계 한글 변환
  const getProcessingStepLabel = (step?: string | null) => {
    if (!step) return "";
    const steps: Record<string, string> = {
      "initializing": "초기화 중",
      "downloading_pdf": "PDF 다운로드",
      "extracting_text": "텍스트 추출",
      "extracting_entities": "엔티티 추출",
      "extracting_relationships": "관계 추출",
      "building_graph": "그래프 구축",
      "generating_embeddings": "임베딩 생성",
      "completed": "완료"
    };
    return steps[step] || step;
  };

  // 세부 단계 한글 변환
  const getSubStepLabel = (subStep: string) => {
    const subSteps: Record<string, string> = {
      "pdf_analysis": "PDF 메타데이터 분석",
      "page_setup": "페이지 정보 확인",
      "page_count_confirmed": "페이지 수 확인 완료",
      "text_layer_extraction": "텍스트 레이어 추출",
      "ocr_required": "OCR 필요",
      "image_detection": "이미지 영역 감지",
      "table_analysis": "표 구조 분석",
      "layout_analysis": "레이아웃 분석",
      "text_normalization": "텍스트 정규화",
      "quality_validation": "품질 검증"
    };
    return subSteps[subStep] || subStep;
  };

  const handleDocumentClick = async (e: React.MouseEvent) => {
    // 이미 처리 중인 문서는 클릭 무시
    if (isBeingProcessed) {
      showInfo("문서가 학습 중입니다. 잠시만 기다려주세요.");
      return;
    }

    // 학습 완료된 문서는 상세 정보 토글
    if (isLearned) {
      setIsDetailExpanded(!isDetailExpanded);
      return;
    }

    // 미학습 문서 클릭시 모달 표시
    if (!isLearned && doc.pdfUrl) {
      setShowLearnModal(true);
      return;
    }
  };

  const handleConfirmLearn = async () => {
    setShowLearnModal(false);
    setIsProcessing(true);
    try {
      // 학습 API 호출
      const response = await fetch(
        `http://localhost:8000/api/v1/crawler/documents/${doc.id}/process`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            pdf_url: doc.pdfUrl,
            insurer: insurer,
            title: doc.name,
          }),
        }
      );

      if (response.ok) {
        showSuccess(`"${doc.name}" 문서 학습을 시작했습니다.`);
        // 즉시 새로고침하여 processing 상태 반영
        if (onRefresh) {
          onRefresh();
          // 추가로 2초 후에도 한번 더 새로고침
          setTimeout(() => onRefresh(), 2000);
        }
        // 성공 시에는 isProcessing을 true로 유지 (서버에서 상태를 받아올 때까지)
      } else {
        const error = await response.json();
        showError(`문서 학습 실패: ${error.detail || "알 수 없는 오류"}`);
        setIsProcessing(false); // 실패한 경우에만 false로
      }
    } catch (error) {
      console.error("Failed to process document:", error);
      showError("문서 학습 요청에 실패했습니다.");
      setIsProcessing(false); // 에러 발생 시에만 false로
    }
  };

  const handleReprocess = async (e: React.MouseEvent) => {
    e.stopPropagation(); // 카드 클릭 이벤트 전파 방지

    const confirmed = window.confirm(
      `"${doc.name}" 문서를 다른 알고리즘으로 재학습하시겠습니까?\n\n` +
      `현재 품질 점수: ${doc.processingDetail?.quality_score || 0}점\n` +
      `다른 알고리즘을 시도하여 더 나은 품질의 텍스트 추출을 시도합니다.`
    );
    if (!confirmed) return;

    setIsProcessing(true);
    setIsDetailExpanded(false);

    try {
      // 문서 상태를 pending으로 변경하고 재학습
      const response = await fetch(
        `http://localhost:8000/api/v1/crawler/documents/${doc.id}/process`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            pdf_url: doc.pdfUrl,
            insurer: insurer,
            title: doc.name,
            force_reprocess: true, // 재처리 플래그
          }),
        }
      );

      if (response.ok) {
        showSuccess(`"${doc.name}" 문서 재학습을 시작했습니다.`);
        if (onRefresh) {
          onRefresh();
          setTimeout(() => onRefresh(), 2000);
        }
      } else {
        const error = await response.json();
        showError(`문서 재학습 실패: ${error.detail || "알 수 없는 오류"}`);
        setIsProcessing(false);
      }
    } catch (error) {
      console.error("Failed to reprocess document:", error);
      showError("문서 재학습 요청에 실패했습니다.");
      setIsProcessing(false);
    }
  };

  const handleReset = async (e: React.MouseEvent) => {
    e.stopPropagation(); // 카드 클릭 이벤트 전파 방지

    const confirmed = window.confirm(
      `"${doc.name}" 문서를 미학습 상태로 초기화하시겠습니까?\n\n` +
      `경고: 학습된 데이터가 모두 삭제되고 처음부터 다시 학습해야 합니다.`
    );
    if (!confirmed) return;

    setIsResetting(true);

    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/crawler/${doc.id}/reset`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (response.ok) {
        showSuccess(`"${doc.name}" 문서가 초기화되었습니다.`);
        if (onRefresh) {
          onRefresh();
        }
      } else {
        const error = await response.json();
        showError(`문서 초기화 실패: ${error.detail || "알 수 없는 오류"}`);
      }
    } catch (error) {
      console.error("Failed to reset document:", error);
      showError("문서 초기화 요청에 실패했습니다.");
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <Card
      className={`cursor-pointer hover:shadow-md transition-shadow ${
        isLearned ? "border-green-200 bg-green-50/30" :
        isBeingProcessed ? "border-blue-200 bg-blue-50/20" :
        "border-orange-200 bg-orange-50/20"
      } ${isBeingProcessed ? "opacity-75 cursor-wait" : ""}`}
      onClick={handleDocumentClick}
    >
      <CardContent className="p-3">
        {/* 단일 라인 레이아웃: 아이콘 | 문서명 | 카테고리 | 판매시점 | 상태 */}
        <div className="flex items-center gap-3">
          {/* 상태 아이콘 */}
          {isBeingProcessed ? (
            <Loader2 className="h-5 w-5 text-blue-600 flex-shrink-0 animate-spin" />
          ) : isLearned ? (
            <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0" />
          ) : (
            <Circle className="h-5 w-5 text-orange-500 flex-shrink-0" />
          )}

          {/* 문서명 (flex-1로 남은 공간 차지) */}
          <span className="font-medium text-sm flex-1 truncate">{doc.name}</span>

          {/* 카테고리 뱃지 */}
          <Badge variant="outline" className="text-xs flex-shrink-0">
            {doc.category}
          </Badge>

          {/* 판매 시점 */}
          <span className="text-sm text-muted-foreground flex-shrink-0">
            {doc.launchDate}
          </span>

          {/* 상태 뱃지 */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <Badge
              variant={isBeingProcessed ? "outline" : isLearned ? "default" : "secondary"}
              className={`${isBeingProcessed ? "bg-blue-100" : isLearned ? "bg-green-600" : "bg-orange-500"}`}
            >
              {isBeingProcessed ? "학습 중..." : isLearned ? "학습 완료" : "미학습"}
            </Badge>

            {/* 학습 완료된 문서에 초기화 버튼 추가 */}
            {isLearned && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleReset}
                disabled={isResetting}
                className="h-6 px-2 text-xs"
              >
                {isResetting ? "초기화 중..." : "초기화"}
              </Button>
            )}
          </div>
        </div>

        {/* 학습 완료 - 품질 정보 표시 */}
        {isLearned && isDetailExpanded && doc.processingDetail && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <div className="bg-green-50 p-3 rounded-md space-y-2">
              <div className="flex items-center justify-between">
                <h5 className="text-sm font-semibold text-green-900">품질 정보</h5>
                <ChevronDown className="h-4 w-4 text-green-600 rotate-180" />
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-600">품질 점수:</span>
                  <span className={`font-bold ${
                    (doc.processingDetail.quality_score || 0) >= 80 ? 'text-green-600' :
                    (doc.processingDetail.quality_score || 0) >= 60 ? 'text-yellow-600' :
                    'text-red-600'
                  }`}>
                    {doc.processingDetail.quality_score || 0}점
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-600">알고리즘:</span>
                  <span className="text-gray-900">{doc.processingDetail.algorithm || 'N/A'}</span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-600">텍스트:</span>
                  <span className="text-gray-900">
                    {(doc.processingDetail.text_length || 0).toLocaleString()} 자
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-600">페이지:</span>
                  <span className="text-gray-900">{doc.processingDetail.total_pages || 0} 페이지</span>
                </div>
              </div>

              {/* 품질 점수가 80점 미만이면 재학습 버튼 표시 */}
              {(doc.processingDetail.quality_score || 0) < 80 && (
                <div className="mt-3 pt-3 border-t border-green-200">
                  <p className="text-xs text-orange-700 mb-2">
                    ⚠️ 품질 점수가 80점 미만입니다. 다른 알고리즘으로 재학습을 권장합니다.
                  </p>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleReprocess}
                    className="w-full text-xs border-orange-300 text-orange-700 hover:bg-orange-50"
                  >
                    <RefreshCw className="h-3 w-3 mr-1" />
                    다른 알고리즘으로 재학습
                  </Button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 처리 진행 상태 표시 */}
        {isBeingProcessed && doc.processingStep && (
          <div className="mt-3 space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">
                {getProcessingStepLabel(doc.processingStep)}
              </span>
              <span className="text-muted-foreground font-medium" suppressHydrationWarning>
                {doc.processingProgress || 0}%
              </span>
            </div>
            <Progress value={doc.processingProgress || 0} className="h-2" />
            <div className="flex flex-wrap gap-1 mt-2">
              {[
                { step: "downloading_pdf", label: "다운로드", threshold: 20 },
                { step: "extracting_text", label: "텍스트", threshold: 40 },
                { step: "extracting_entities", label: "엔티티", threshold: 60 },
                { step: "extracting_relationships", label: "관계", threshold: 80 },
                { step: "building_graph", label: "그래프", threshold: 90 },
                { step: "generating_embeddings", label: "임베딩", threshold: 95 }
              ].map((item) => (
                <span
                  key={item.step}
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    (doc.processingProgress || 0) >= item.threshold
                      ? "bg-blue-100 text-blue-700"
                      : "bg-gray-100 text-gray-500"
                  }`}
                >
                  {item.label}
                </span>
              ))}
            </div>

            {/* 세부 진행 상황 표시 (처리 상세 정보가 있을 때만) */}
            {doc.processingDetail && (
              <div className="mt-3 border-t pt-3">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setIsDetailExpanded(!isDetailExpanded);
                  }}
                  className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 transition-colors"
                >
                  <ChevronDown
                    className={`h-4 w-4 transition-transform ${isDetailExpanded ? 'rotate-180' : ''}`}
                  />
                  <span>{isDetailExpanded ? '세부 진행 숨기기' : '세부 진행 보기'}</span>
                </button>

                {isDetailExpanded && (
                  <div className="mt-3 space-y-2 bg-blue-50/50 p-3 rounded-md border border-blue-100">
                    <div className="flex items-center justify-between text-xs text-blue-900">
                      <span className="font-medium">
                        {getSubStepLabel(doc.processingDetail.sub_step)}
                      </span>
                    </div>

                    {doc.processingDetail.message && (
                      <p className="text-xs text-blue-700">
                        {doc.processingDetail.message}
                      </p>
                    )}

                    {/* 페이지 정보 표시 */}
                    {doc.processingDetail.total_pages && (
                      <div className="flex items-center gap-2 text-xs text-blue-600">
                        <FileText className="h-3 w-3" />
                        <span>
                          {doc.processingDetail.current_page
                            ? `${doc.processingDetail.current_page}/${doc.processingDetail.total_pages} 페이지`
                            : `총 ${doc.processingDetail.total_pages} 페이지`
                          }
                        </span>
                        {/* 페이지별 진행률 */}
                        {doc.processingDetail.percent && (
                          <span className="text-blue-500 font-medium">
                            ({doc.processingDetail.percent}%)
                          </span>
                        )}
                      </div>
                    )}

                    {/* 처리 속도 및 예상 완료 시간 */}
                    {doc.processingDetail.pages_per_second && (
                      <div className="flex items-center gap-3 text-xs">
                        <div className="flex items-center gap-1 text-green-600">
                          <span className="font-medium">속도:</span>
                          <span>{doc.processingDetail.pages_per_second} 페이지/초</span>
                        </div>
                        {doc.processingDetail.estimated_time && (
                          <div className="flex items-center gap-1 text-orange-600">
                            <span className="font-medium">예상 완료:</span>
                            <span>약 {doc.processingDetail.estimated_time} 남음</span>
                          </div>
                        )}
                      </div>
                    )}

                    {/* 처리 시간 정보 (완료 시) */}
                    {doc.processingDetail.processing_time_seconds && (
                      <div className="text-xs text-purple-600">
                        총 처리 시간: {doc.processingDetail.processing_time_seconds}초
                      </div>
                    )}

                    {/* 텍스트 길이 정보 */}
                    {doc.processingDetail.text_length && (
                      <div className="text-xs text-blue-600">
                        추출된 텍스트: {doc.processingDetail.text_length.toLocaleString()} 자
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </CardContent>

      {/* 미학습 문서 학습 확인 모달 */}
      {showLearnModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowLearnModal(false)}>
          <Card className="max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <CardHeader className="border-b">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-full">
                  <FileText className="h-6 w-6 text-blue-600" />
                </div>
                <CardTitle className="text-lg">문서 학습 시작</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="pt-6 space-y-4">
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-900">
                  다음 문서를 학습하시겠습니까?
                </p>
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="text-sm font-semibold text-gray-900">{doc.name}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <Badge variant="outline" className="text-xs">
                      {doc.category}
                    </Badge>
                    <span className="text-xs text-gray-500">{doc.launchDate}</span>
                  </div>
                </div>
              </div>

              <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                <p className="text-xs text-blue-800">
                  이 작업은 몇 분 정도 소요될 수 있습니다. 학습이 진행되는 동안 문서의 상태를 실시간으로 확인할 수 있습니다.
                </p>
              </div>
            </CardContent>
            <div className="border-t p-4 flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => setShowLearnModal(false)}
              >
                취소
              </Button>
              <Button
                onClick={handleConfirmLearn}
                className="bg-blue-600 hover:bg-blue-700"
              >
                <FileText className="h-4 w-4 mr-1" />
                학습 시작
              </Button>
            </div>
          </Card>
        </div>
      )}
    </Card>
  );
}
