"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

// 보험사 데이터 타입
interface Insurer {
  id: string;
  name: string;
  type: "생명보험" | "손해보험";
  crawlUrl: string;
  status: "active" | "inactive" | "testing";
  lastCrawled: string | null;
  documentCount: number;
}

// 초기 보험사 목록 (30개)
const INITIAL_INSURERS: Insurer[] = [
  // 생명보험 15개
  { id: "1", name: "삼성생명", type: "생명보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "2", name: "한화생명", type: "생명보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "3", name: "교보생명", type: "생명보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "4", name: "DB생명", type: "생명보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "5", name: "신한라이프", type: "생명보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "6", name: "메트라이프생명", type: "생명보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "7", name: "처브라이프", type: "생명보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "8", name: "푸르덴셜생명", type: "생명보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "9", name: "AIA생명", type: "생명보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "10", name: "DGB생명", type: "생명보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "11", name: "ABL생명", type: "생명보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "12", name: "KB라이프생명", type: "생명보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "13", name: "BNP파리바카디프생명", type: "생명보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "14", name: "KDB생명", type: "생명보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "15", name: "IBK연금보험", type: "생명보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },

  // 손해보험 15개
  { id: "16", name: "삼성화재", type: "손해보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "17", name: "현대해상", type: "손해보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "18", name: "DB손해보험", type: "손해보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "19", name: "KB손해보험", type: "손해보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "20", name: "메리츠화재", type: "손해보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "21", name: "한화손해보험", type: "손해보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "22", name: "롯데손해보험", type: "손해보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "23", name: "MG손해보험", type: "손해보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "24", name: "흥국화재", type: "손해보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "25", name: "캐롯손해보험", type: "손해보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "26", name: "AXA손해보험", type: "손해보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "27", name: "하나손해보험", type: "손해보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "28", name: "NH농협손해보험", type: "손해보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "29", name: "BNK손해보험", type: "손해보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
  { id: "30", name: "THE K손해보험", type: "손해보험", crawlUrl: "", status: "inactive", lastCrawled: null, documentCount: 0 },
];

const statusColors = {
  active: "bg-green-500 text-white",
  inactive: "bg-gray-400 text-white",
  testing: "bg-yellow-500 text-white",
};

const statusLabels = {
  active: "활성",
  inactive: "미설정",
  testing: "테스트중",
};

export default function MetadataAdminPage() {
  const [insurers, setInsurers] = useState<Insurer[]>(INITIAL_INSURERS);
  const [selectedInsurer, setSelectedInsurer] = useState<Insurer | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUrl, setEditingUrl] = useState("");
  const [filterType, setFilterType] = useState<"all" | "생명보험" | "손해보험">("all");
  const [filterStatus, setFilterStatus] = useState<"all" | "active" | "inactive" | "testing">("all");
  const [crawlLogs, setCrawlLogs] = useState<string[]>([]);
  const [crawlStep, setCrawlStep] = useState(0);
  const [discoveredFiles, setDiscoveredFiles] = useState<string[]>([]);

  // 필터링된 보험사 목록
  const filteredInsurers = insurers.filter((insurer) => {
    if (filterType !== "all" && insurer.type !== filterType) return false;
    if (filterStatus !== "all" && insurer.status !== filterStatus) return false;
    return true;
  });

  // 보험사 선택 (모달 열기)
  const handleSelectInsurer = (insurer: Insurer) => {
    setSelectedInsurer(insurer);
    setEditingUrl(insurer.crawlUrl);
    setIsModalOpen(true);
    setCrawlLogs([]);
    setCrawlStep(0);
  };

  // 모달 닫기
  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedInsurer(null);
    setEditingUrl("");
    setCrawlLogs([]);
    setCrawlStep(0);
    setDiscoveredFiles([]);
  };

  // URL 저장
  const handleSaveUrl = () => {
    if (!selectedInsurer) return;

    setInsurers((prev) =>
      prev.map((ins) =>
        ins.id === selectedInsurer.id
          ? { ...ins, crawlUrl: editingUrl, status: editingUrl ? "inactive" : "inactive" }
          : ins
      )
    );

    // 선택된 보험사 정보도 업데이트
    setSelectedInsurer({
      ...selectedInsurer,
      crawlUrl: editingUrl,
    });

    alert(`${selectedInsurer.name} URL이 저장되었습니다.`);
  };

  // 샘플 크롤링 시작
  const handleTestCrawl = async () => {
    if (!selectedInsurer || !editingUrl) {
      alert("크롤링 URL을 먼저 입력해주세요.");
      return;
    }

    // 테스트 상태로 변경
    setInsurers((prev) =>
      prev.map((ins) =>
        ins.id === selectedInsurer.id ? { ...ins, status: "testing" } : ins
      )
    );

    setSelectedInsurer({ ...selectedInsurer, status: "testing" });

    // 크롤링 시뮬레이션
    setCrawlLogs([]);
    setCrawlStep(1);
    addLog("크롤링 시작...");

    await sleep(1000);
    addLog("Playwright 브라우저 실행");

    await sleep(1500);
    addLog(`페이지 로딩: ${editingUrl}`);
    setCrawlStep(2);

    await sleep(2000);
    addLog("HTML 파싱 완료");
    addLog("문서 목록 테이블 탐색 중...");

    await sleep(1500);
    setCrawlStep(3);
    addLog("문서 목록 테이블 발견");

    await sleep(1000);
    addLog("HTML 파일 저장 완료: crawl_result.html");
    setCrawlStep(4);

    await sleep(1500);
    addLog("🤖 LLM 분석 시작 (Claude Sonnet 4.5)");
    addLog("HTML에서 약관 파일명 추출 중...");

    await sleep(2000);
    addLog("✅ 분석 완료! 발견된 문서:");

    // 샘플 파일명 목록
    const sampleFiles = [
      `${selectedInsurer.name}_종합보험약관_v2.0.pdf`,
      `${selectedInsurer.name}_암보험특약_안내서.pdf`,
      `${selectedInsurer.name}_실손의료보험_약관.pdf`,
      `${selectedInsurer.name}_간편심사_가입설계서.pdf`,
      `${selectedInsurer.name}_보장내용_변경안내.pdf`,
    ];

    setDiscoveredFiles(sampleFiles);

    sampleFiles.forEach((file, index) => {
      addLog(`  ${index + 1}. ${file}`);
    });

    await sleep(500);
    addLog(`총 ${sampleFiles.length}개 문서 발견`);
    addLog("크롤링 테스트 완료!");

    // 완료 후 활성 상태로 변경
    setTimeout(() => {
      setInsurers((prev) =>
        prev.map((ins) =>
          ins.id === selectedInsurer.id ? { ...ins, status: "active", documentCount: 12, lastCrawled: new Date().toISOString() } : ins
        )
      );
      setSelectedInsurer({ ...selectedInsurer, status: "active", documentCount: 12, lastCrawled: new Date().toISOString() });
    }, 500);
  };

  const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

  const addLog = (message: string) => {
    const timestamp = new Date().toLocaleTimeString("ko-KR");
    setCrawlLogs((prev) => [...prev, `[${timestamp}] ${message}`]);
  };

  // 통계
  const stats = {
    total: insurers.length,
    active: insurers.filter((i) => i.status === "active").length,
    inactive: insurers.filter((i) => i.status === "inactive").length,
    testing: insurers.filter((i) => i.status === "testing").length,
  };

  return (
    <div className="container mx-auto py-8 px-4 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">보험사 크롤링 관리</h1>
        <p className="text-gray-600">
          보험사를 클릭하여 크롤링 URL을 설정하고 샘플 크롤링을 테스트하세요
        </p>
      </div>

      {/* 통계 카드 */}
      <div className="grid gap-4 md:grid-cols-4 mb-6">
        <Card
          className="cursor-pointer hover:shadow-lg transition-shadow"
          onClick={() => setFilterStatus("all")}
        >
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              전체 보험사
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}개</div>
            <p className="text-xs text-gray-500 mt-1">클릭하여 전체 보기</p>
          </CardContent>
        </Card>

        <Card
          className="cursor-pointer hover:shadow-lg transition-shadow"
          onClick={() => setFilterStatus("active")}
        >
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              활성
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.active}개</div>
            <p className="text-xs text-gray-500 mt-1">크롤링 설정 완료</p>
          </CardContent>
        </Card>

        <Card
          className="cursor-pointer hover:shadow-lg transition-shadow"
          onClick={() => setFilterStatus("testing")}
        >
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              테스트중
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{stats.testing}개</div>
            <p className="text-xs text-gray-500 mt-1">샘플 크롤링 진행중</p>
          </CardContent>
        </Card>

        <Card
          className="cursor-pointer hover:shadow-lg transition-shadow border-2 border-orange-200"
          onClick={() => setFilterStatus("inactive")}
        >
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 flex items-center justify-between">
              미설정
              <Badge className="bg-orange-500 text-white">설정필요</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{stats.inactive}개</div>
            <p className="text-xs text-orange-600 mt-1 font-medium">
              ⚠️ URL 설정이 필요합니다
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 미설정 보험사 빠른 작업 패널 */}
      {filterStatus === "inactive" && stats.inactive > 0 && (
        <Card className="mb-6 border-orange-200 bg-orange-50">
          <CardHeader>
            <CardTitle className="text-orange-800 flex items-center gap-2">
              ⚡ 빠른 작업
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-orange-700 mb-4">
              미설정된 {stats.inactive}개 보험사의 크롤링 URL을 빠르게 설정하세요.
            </p>
            <div className="flex gap-2">
              <Button
                variant="default"
                className="bg-orange-600 hover:bg-orange-700"
                onClick={() => {
                  const firstInactive = insurers.find((i) => i.status === "inactive");
                  if (firstInactive) {
                    handleSelectInsurer(firstInactive);
                  }
                }}
              >
                첫 번째 보험사부터 설정하기
              </Button>
              <Button
                variant="secondary"
                onClick={() => {
                  const confirmed = confirm(
                    "자동 크롤링 URL 추천 기능을 사용하시겠습니까?\n\n" +
                    "보험사 공식 홈페이지에서 약관 페이지를 자동으로 찾아 추천해드립니다.\n" +
                    "(베타 기능)"
                  );
                  if (confirmed) {
                    alert("자동 URL 추천 기능은 곧 제공될 예정입니다.");
                  }
                }}
              >
                🤖 자동 URL 추천
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 보험사 그리드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {/* 필터 섹션 */}
        <div className="col-span-full mb-4">
          <div className="flex gap-2">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value as any)}
              className="border rounded px-3 py-2 text-sm"
            >
              <option value="all">전체 유형</option>
              <option value="생명보험">생명보험</option>
              <option value="손해보험">손해보험</option>
            </select>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as any)}
              className="border rounded px-3 py-2 text-sm"
            >
              <option value="all">모든 상태</option>
              <option value="active">활성</option>
              <option value="testing">테스트중</option>
              <option value="inactive">미설정</option>
            </select>
          </div>
        </div>

        {/* 보험사 카드 */}
        {filteredInsurers.map((insurer) => (
          <Card
            key={insurer.id}
            className="cursor-pointer hover:shadow-lg transition-all hover:scale-105"
            onClick={() => handleSelectInsurer(insurer)}
          >
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <CardTitle className="text-base">{insurer.name}</CardTitle>
                <Badge className={statusColors[insurer.status]}>
                  {statusLabels[insurer.status]}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-xs text-gray-500 mb-2">{insurer.type}</div>
              {insurer.crawlUrl && (
                <div className="text-xs text-blue-600 truncate mb-2" title={insurer.crawlUrl}>
                  🔗 {insurer.crawlUrl}
                </div>
              )}
              {insurer.documentCount > 0 && (
                <div className="text-xs text-green-600">
                  📄 문서 {insurer.documentCount}개 발견
                </div>
              )}
              {!insurer.crawlUrl && (
                <div className="text-xs text-orange-600">
                  ⚠️ URL 미설정
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 모달 */}
      {isModalOpen && selectedInsurer && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            {/* 모달 헤더 */}
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold">{selectedInsurer.name}</h2>
                <p className="text-sm text-gray-600">{selectedInsurer.type}</p>
              </div>
              <button
                onClick={handleCloseModal}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ✕
              </button>
            </div>

            {/* 모달 내용 */}
            <div className="p-6 space-y-6">
              {/* 기본 정보 */}
              <div>
                <h3 className="font-semibold mb-3">기본 정보</h3>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-600">상태:</span>
                    <Badge className={statusColors[selectedInsurer.status]}>
                      {statusLabels[selectedInsurer.status]}
                    </Badge>
                  </div>
                  {selectedInsurer.lastCrawled && (
                    <div className="text-sm text-gray-600">
                      마지막 크롤링: {new Date(selectedInsurer.lastCrawled).toLocaleString("ko-KR")}
                    </div>
                  )}
                  {selectedInsurer.documentCount > 0 && (
                    <div className="text-sm text-green-600 font-medium">
                      📄 발견된 문서: {selectedInsurer.documentCount}개
                    </div>
                  )}
                </div>
              </div>

              {/* URL 설정 */}
              <div>
                <h3 className="font-semibold mb-3">크롤링 URL 설정</h3>
                <label className="block text-sm font-medium mb-2">
                  약관/상품 목록 페이지 URL
                </label>
                <input
                  type="text"
                  value={editingUrl}
                  onChange={(e) => setEditingUrl(e.target.value)}
                  placeholder="https://www.example.com/products"
                  className="w-full border-2 border-gray-300 rounded-lg px-4 py-3 mb-2 text-base bg-white text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all font-mono"
                />
                <p className="text-xs text-gray-500">
                  보험 약관이나 상품이 리스트로 나열된 페이지의 URL을 입력하세요
                </p>
              </div>

              {/* 버튼 */}
              <div className="flex gap-2">
                <Button onClick={handleSaveUrl} variant="default">
                  💾 URL 저장
                </Button>
                <Button
                  onClick={handleTestCrawl}
                  disabled={!editingUrl || selectedInsurer.status === "testing"}
                  className="bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-300"
                >
                  {selectedInsurer.status === "testing" ? "⏳ 테스트 진행중..." : "🧪 샘플 크롤링 테스트"}
                </Button>
              </div>

              {/* 크롤링 결과 */}
              {(selectedInsurer.status === "testing" || crawlLogs.length > 0) && (
                <div>
                  <h3 className="font-semibold mb-3">크롤링 진행 상황</h3>

                  {/* 진행 단계 */}
                  <div className="space-y-3 mb-4">
                    <div className={`flex items-center gap-3 ${crawlStep >= 1 ? "" : "opacity-30"}`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm ${crawlStep >= 1 ? "bg-blue-500" : "bg-gray-300"}`}>
                        {crawlStep > 1 ? "✓" : "1"}
                      </div>
                      <div>
                        <div className="font-medium">Playwright 페이지 분석</div>
                        <div className="text-xs text-gray-500">
                          {crawlStep === 1 ? "진행중..." : crawlStep > 1 ? "완료" : "대기중"}
                        </div>
                      </div>
                    </div>

                    <div className={`flex items-center gap-3 ${crawlStep >= 2 ? "" : "opacity-30"}`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm ${crawlStep >= 2 ? "bg-blue-500" : "bg-gray-300"}`}>
                        {crawlStep > 2 ? "✓" : "2"}
                      </div>
                      <div>
                        <div className="font-medium">HTML 파싱 및 분석</div>
                        <div className="text-xs text-gray-500">
                          {crawlStep === 2 ? "진행중..." : crawlStep > 2 ? "완료" : "대기중"}
                        </div>
                      </div>
                    </div>

                    <div className={`flex items-center gap-3 ${crawlStep >= 3 ? "" : "opacity-30"}`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm ${crawlStep >= 3 ? "bg-blue-500" : "bg-gray-300"}`}>
                        {crawlStep > 3 ? "✓" : "3"}
                      </div>
                      <div>
                        <div className="font-medium">HTML 저장</div>
                        <div className="text-xs text-gray-500">
                          {crawlStep === 3 ? "진행중..." : crawlStep > 3 ? "완료" : "대기중"}
                        </div>
                      </div>
                    </div>

                    <div className={`flex items-center gap-3 ${crawlStep >= 4 ? "" : "opacity-30"}`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm ${crawlStep >= 4 ? "bg-green-500" : "bg-gray-300"}`}>
                        {crawlStep >= 4 ? "✓" : "4"}
                      </div>
                      <div>
                        <div className="font-medium">🤖 LLM 분석 (파일명 추출)</div>
                        <div className="text-xs text-gray-500">
                          {crawlStep === 4 ? "완료" : "대기중"}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* 로그 */}
                  {crawlLogs.length > 0 && (
                    <div className="p-4 bg-gray-900 text-green-400 rounded font-mono text-xs max-h-60 overflow-y-auto">
                      {crawlLogs.map((log, index) => (
                        <div key={index}>{log}</div>
                      ))}
                    </div>
                  )}

                  {/* 발견된 파일 목록 */}
                  {discoveredFiles.length > 0 && (
                    <div className="mt-6 p-4 bg-green-50 border-2 border-green-200 rounded-lg">
                      <h4 className="font-semibold text-green-800 mb-3 flex items-center gap-2">
                        📄 발견된 약관 파일 ({discoveredFiles.length}개)
                      </h4>
                      <div className="space-y-2">
                        {discoveredFiles.map((file, index) => (
                          <div
                            key={index}
                            className="flex items-start gap-2 p-3 bg-white rounded border border-green-200 hover:border-green-400 transition-colors"
                          >
                            <div className="flex-shrink-0 w-6 h-6 bg-green-500 text-white rounded-full flex items-center justify-center text-xs font-bold">
                              {index + 1}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="text-sm font-medium text-gray-900 break-all">
                                {file}
                              </div>
                            </div>
                            <div className="flex-shrink-0">
                              <button className="text-xs text-blue-600 hover:text-blue-800 hover:underline">
                                상세보기
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded">
                        <p className="text-xs text-blue-800">
                          💡 <strong>다음 단계:</strong> 이 파일들을 학습 대기열에 추가하거나 개별적으로 다운로드할 수 있습니다.
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* 모달 푸터 */}
            <div className="sticky bottom-0 bg-gray-50 border-t px-6 py-4 flex justify-end">
              <Button onClick={handleCloseModal} variant="secondary">
                닫기
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
