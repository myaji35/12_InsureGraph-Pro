"use client";

import { useState, useEffect } from "react";
import { X, Plus, Trash2, Edit2, ExternalLink, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { showSuccess, showError } from "@/lib/toast-config";
import type { CrawlerUrl } from "@insuregraph/shared-types";

interface CrawlerUrlManagementModalProps {
  isOpen: boolean;
  onClose: () => void;
  insurer: string;
}

export default function CrawlerUrlManagementModal({
  isOpen,
  onClose,
  insurer,
}: CrawlerUrlManagementModalProps) {
  const [urls, setUrls] = useState<CrawlerUrl[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [isAddingNew, setIsAddingNew] = useState(false);

  // 폼 상태
  const [formUrl, setFormUrl] = useState("");
  const [formDescription, setFormDescription] = useState("");

  useEffect(() => {
    if (isOpen) {
      loadUrls();
    }
  }, [isOpen, insurer]);

  const loadUrls = async () => {
    try {
      setIsLoading(true);
      // API에서 URL 목록 가져오기
      const apiBaseUrl =
        process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";
      const response = await fetch(
        `${apiBaseUrl}/v1/crawler/urls?insurer=${encodeURIComponent(insurer)}`
      );

      if (!response.ok) {
        throw new Error("Failed to fetch URLs");
      }

      const data = await response.json();
      setUrls(data.items || []);
    } catch (error) {
      console.error("Failed to load URLs:", error);
      showError("URL 목록을 불러오는데 실패했습니다");
      setUrls([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddNew = () => {
    setIsAddingNew(true);
    setFormUrl("");
    setFormDescription("");
  };

  const handleEdit = (url: CrawlerUrl) => {
    setEditingId(url.id);
    setFormUrl(url.url);
    setFormDescription(url.description);
  };

  const handleSave = async () => {
    if (!formUrl.trim()) {
      showError("URL을 입력해주세요");
      return;
    }

    try {
      const apiBaseUrl =
        process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";

      if (isAddingNew) {
        // POST: 새 URL 추가
        const response = await fetch(`${apiBaseUrl}/v1/crawler/urls`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            insurer: insurer,
            url: formUrl,
            description: formDescription,
            enabled: true,
          }),
        });

        if (!response.ok) {
          throw new Error("Failed to create URL");
        }

        showSuccess("URL이 추가되었습니다");
      } else if (editingId) {
        // PUT: URL 수정
        const response = await fetch(
          `${apiBaseUrl}/v1/crawler/urls/${editingId}`,
          {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              url: formUrl,
              description: formDescription,
            }),
          }
        );

        if (!response.ok) {
          throw new Error("Failed to update URL");
        }

        showSuccess("URL이 수정되었습니다");
      } else {
        return;
      }

      // Reload URLs from API
      await loadUrls();

      setIsAddingNew(false);
      setEditingId(null);
      setFormUrl("");
      setFormDescription("");
    } catch (error) {
      console.error("Failed to save URL:", error);
      showError("URL 저장에 실패했습니다");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("이 URL을 삭제하시겠습니까?")) return;

    try {
      const apiBaseUrl =
        process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";

      const response = await fetch(`${apiBaseUrl}/v1/crawler/urls/${id}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Failed to delete URL");
      }

      showSuccess("URL이 삭제되었습니다");
      await loadUrls();
    } catch (error) {
      console.error("Failed to delete URL:", error);
      showError("URL 삭제에 실패했습니다");
    }
  };

  const handleToggleEnabled = async (id: string) => {
    try {
      const apiBaseUrl =
        process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";

      // Find current URL to toggle its enabled status
      const currentUrl = urls.find((u) => u.id === id);
      if (!currentUrl) return;

      const response = await fetch(`${apiBaseUrl}/v1/crawler/urls/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          enabled: !currentUrl.enabled,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to toggle URL");
      }

      showSuccess("상태가 변경되었습니다");
      await loadUrls();
    } catch (error) {
      console.error("Failed to toggle URL:", error);
      showError("상태 변경에 실패했습니다");
    }
  };

  const handleCancel = () => {
    setIsAddingNew(false);
    setEditingId(null);
    setFormUrl("");
    setFormDescription("");
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 dark:bg-black/70"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative w-full max-w-3xl bg-white dark:bg-dark-surface rounded-lg shadow-xl">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-dark-border">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                크롤링 URL 관리
              </h2>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                {insurer}의 크롤링 대상 URL을 관리합니다
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6">
            {/* Add New Button */}
            {!isAddingNew && !editingId && (
              <div className="mb-4">
                <Button onClick={handleAddNew} className="w-full">
                  <Plus className="h-4 w-4 mr-2" />
                  새 URL 추가
                </Button>
              </div>
            )}

            {/* Add/Edit Form */}
            {(isAddingNew || editingId) && (
              <div className="mb-6 p-4 border border-gray-200 dark:border-dark-border rounded-lg bg-gray-50 dark:bg-dark-elevated">
                <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">
                  {isAddingNew ? "새 URL 추가" : "URL 수정"}
                </h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      URL *
                    </label>
                    <input
                      type="url"
                      value={formUrl}
                      onChange={(e) => setFormUrl(e.target.value)}
                      placeholder="https://example.com/products"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-dark-border rounded-lg bg-white dark:bg-dark-surface text-gray-900 dark:text-gray-100"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      설명
                    </label>
                    <input
                      type="text"
                      value={formDescription}
                      onChange={(e) => setFormDescription(e.target.value)}
                      placeholder="URL 용도 설명"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-dark-border rounded-lg bg-white dark:bg-dark-surface text-gray-900 dark:text-gray-100"
                    />
                  </div>
                  <div className="flex gap-2">
                    <Button onClick={handleSave} className="flex-1">
                      <Save className="h-4 w-4 mr-2" />
                      저장
                    </Button>
                    <Button
                      onClick={handleCancel}
                      variant="outline"
                      className="flex-1"
                    >
                      취소
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* URL List */}
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 dark:border-primary-400"></div>
              </div>
            ) : urls.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-600 dark:text-gray-400">
                  등록된 URL이 없습니다
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {urls.map((url) => (
                  <div
                    key={url.id}
                    className={`p-4 border rounded-lg ${
                      url.enabled
                        ? "border-gray-200 dark:border-dark-border bg-white dark:bg-dark-surface"
                        : "border-gray-200 dark:border-dark-border bg-gray-50 dark:bg-dark-elevated opacity-60"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <a
                            href={url.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary-600 dark:text-primary-400 hover:underline text-sm font-medium flex items-center gap-1 truncate"
                          >
                            {url.url}
                            <ExternalLink className="h-3 w-3 flex-shrink-0" />
                          </a>
                        </div>
                        {url.description && (
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {url.description}
                          </p>
                        )}
                      </div>

                      <div className="flex items-center gap-2 flex-shrink-0">
                        {/* Enable/Disable Toggle */}
                        <button
                          onClick={() => handleToggleEnabled(url.id)}
                          className={`px-3 py-1 rounded text-xs font-medium ${
                            url.enabled
                              ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
                              : "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400"
                          }`}
                        >
                          {url.enabled ? "활성화" : "비활성화"}
                        </button>

                        {/* Edit Button */}
                        <button
                          onClick={() => handleEdit(url)}
                          className="p-2 text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400"
                          title="수정"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>

                        {/* Delete Button */}
                        <button
                          onClick={() => handleDelete(url.id)}
                          className="p-2 text-gray-600 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400"
                          title="삭제"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 p-6 border-t border-gray-200 dark:border-dark-border">
            <Button onClick={onClose} variant="outline">
              닫기
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
