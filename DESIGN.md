# Design System Authority (DESIGN.md)
<!-- visual-vocabulary-agent:design-system 2.0 -->

Tài liệu này là **Quyền lực Thiết kế (Visual Authority)** duy nhất của dự án **Visual Vocabulary Agent (VVA)**. Mọi quyết định về giao diện, mã màu, font chữ, bố cục và component bắt buộc phải tuân theo các đặc tả dưới đây.

---

## 1. Nền tảng Nhận diện Trực quan (Brand & Visual Identity)

- **Phong cách chủ đạo:** Modern EdTech kết hợp Clean Flat & Soft Depth. Không sử dụng các gradient tím-hồng AI slop ngẫu nhiên; tập trung vào tính tương phản cao, chống mỏi mắt và bố cục dạng Bento Grid khoa học.
- **Tông giọng & Cảm xúc:** Trực quan (Visual), Thân thiện (Friendly), Đáng tin cậy (Authoritative), Khích lệ người học (Motivating).
- **Màu nền chống chói:** `#F8FAFC` (Slate-50) thay thế cho màu trắng tinh chói mắt thông thường.

---

## 2. Hệ Thống Design Tokens (CSS Variables)

Tất cả các biến được định nghĩa tại `frontend/assets/styles/tokens.css`:

### A. Bảng màu (Color System & WCAG AA Ratios)
| Token | Hex Code | Độ tương phản chữ (Contrast Ratio) | Vai trò sử dụng |
| :--- | :---: | :---: | :--- |
| `--color-primary-600` | `#4F46E5` | **8.4:1** trên nền trắng | Màu nhận diện chính (Indigo), nút CTA chính, active navigation |
| `--color-primary-700` | `#4338CA` | **10.1:1** trên nền trắng | Trạng thái Hover của nút chính |
| `--color-accent-600` | `#059669` | **4.6:1** trên nền trắng | Màu thành công, biểu thị phát âm chuẩn $\ge 80\%$, chuỗi học streak |
| `--color-ipa-600` | `#7C3AED` | **6.5:1** trên nền trắng | Màu nhấn cho ngữ âm, bảng 44 âm IPA, audio trigger |
| `--color-warning-500`| `#F59E0B` | **3.8:1** (tiêu đề) / Dark text | Điểm phát âm trung bình (60-79%), trạng thái cần lưu ý |
| `--color-error-600` | `#DC2626` | **5.4:1** trên nền trắng | Màu lỗi, cảnh báo phát âm sai ($<60\%$), nút thu âm recording |
| `--color-bg-app` | `#F8FAFC` | - | Nền toàn trang, chống lóa mắt |
| `--color-surface` | `#FFFFFF` | - | Nền của các khối Card, Modal, Dropdown |
| `--color-text-primary`| `#0F172A` | **15.8:1** trên `#F8FAFC` (AAA) | Văn bản chính, tiêu đề H1-H6 |
| `--color-text-secondary`| `#475569` | **5.9:1** trên `#F8FAFC` (AA) | Văn bản phụ, nhãn phụ, mô tả tính năng |

### B. Thang Typography (Modular Scale 1.25)
- **Font gia đình:** `'Plus Jakarta Sans', sans-serif` cho giao diện chính; font hỗ trợ ký tự ngữ âm IPA chuẩn quốc tế.
- **Bậc kích thước chữ:**
  - `text-xs`: 12px (0.75rem) - Badge, nhãn phụ, timestamp.
  - `text-sm`: 14px (0.875rem) - Text nút bấm, body text phụ, bảng dữ liệu.
  - `text-base`: 16px (1rem) - Body text chuẩn, nội dung bài học.
  - `text-lg`: 18px (1.125rem) - Tiêu đề card, phiên âm IPA nổi bật.
  - `text-xl`: 20px (1.25rem) - Tiêu đề phụ của các mục lớn.
  - `text-2xl`: 24px (1.5rem) - Tiêu đề phân hệ chính.
  - `text-3xl`: 30px (1.875rem) - Tiêu đề Hero trang chủ.

### C. Nhịp điệu khoảng cách (8pt Grid Spacing Scale)
- `space-1`: 4px | `space-2`: 8px | `space-3`: 12px | `space-4`: 16px | `space-5`: 20px | `space-6`: 24px | `space-8`: 32px | `space-12`: 48px.
- **Quy tắc:** Margin và Padding giữa các component luôn là bội số của 4px hoặc 8px.

### D. Bo góc (Border Radius) & Độ nổi khối (Elevations)
- `radius-sm`: 6px (Input, nút nhỏ)
- `radius-md`: 10px (Nút chuẩn, dropdown, thẻ từ con)
- `radius-lg`: 16px (Signature Card - thẻ bài học, modal con)
- `radius-xl`: 24px (Hero card, Modal chính)
- `radius-full`: 9999px (Pill, Badge, Avatar)
- **Shadows:** Sử dụng bóng đổ đa lớp khuyếch tán (`--shadow-sm`, `--shadow-md`, `--shadow-lg`), loại bỏ hoàn toàn bóng đen gắt cục mịch.

---

## 3. Tiêu chuẩn Kỹ thuật Bắt buộc (Craft Floor)

1. **Biểu tượng (Iconography):** Tuyệt đối không dùng emoji (📷, 🔊, 💡) làm icon giao diện chính. Bắt buộc dùng SVG hoặc thư viện **FontAwesome 6** (`fa-solid`, `fa-regular`).
2. **Khu vực bấm cảm ứng (Touch Target):** Mọi nút bấm, icon button, hoặc phần tử tương tác trên màn hình cảm ứng phải đạt kích thước tối thiểu **$44 \times 44\text{px}$**.
3. **Trạng thái tương tác rõ nét:**
   - `cursor: pointer` trên mọi phần tử nhấp được.
   - `active`: hiệu ứng thu nhỏ nhẹ (`transform: scale(0.98)`).
   - `focus-visible`: vòng sáng nổi bật `box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.35)`.
4. **Bố cục co giãn 4 Breakpoints:**
   - Mobile: 375px+
   - Tablet: 768px+
   - Laptop: 1024px+
   - Desktop: 1440px+

---

## 4. Đặc tả Trạng thái Màn hình (States Matrix)

Mọi phân hệ trong ứng dụng bắt buộc phải thiết kế hoàn chỉnh 4 trạng thái:
- **Empty State:** Có icon minh họa, tiêu đề giải thích và nút hành động rõ ràng (Call-to-Action).
- **Loading State:** Skeleton shimmer loaders khớp với khung bố cục thật, tuyệt đối không để màn hình trắng hoặc xoay spinner vô định.
- **Error State:** Nêu rõ nguyên nhân (ví dụ: Không tìm thấy vật thể / Quyền mic bị từ chối) kèm nút "Thử lại".
- **Success State:** Dữ liệu hiển thị rõ ràng, phân cấp thị giác mạch lạc.

