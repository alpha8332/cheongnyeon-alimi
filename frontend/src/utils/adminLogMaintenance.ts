/**
 * Archive delete typed confirm helpers (Frontend 08 / FE8-04).
 */

export function isArchiveDeleteConfirmValid(
  fileId: string,
  typedConfirm: string,
): boolean {
  return typedConfirm.trim() === fileId.trim() && fileId.trim().length > 0;
}

export function buildArchiveDeleteConfirmLabel(fileId: string): string {
  return `삭제하려면 file_id "${fileId}"를 입력하세요`;
}
