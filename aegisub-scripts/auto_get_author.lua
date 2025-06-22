script_name = "Lấy Tên Tác Giả Từ Dòng Phụ Đề"  -- Tên của macro
script_description = "Script này sẽ tự động lấy tên tác giả từ dòng có cấu trúc [TENTACGIA:...], sau đó gán tên tác giả vào cột tác giả và xoá tên tác giả khỏi dòng phụ đề đó"  -- Mô tả chức năng của macro
script_author = "yngpiu"  -- Tác giả của macro
script_version = "1.0"  -- Phiên bản của macro

-- Hàm kiểm tra xem chuỗi str có bắt đầu bằng chuỗi start không
local function starts_with(str, start)
    return str:sub(1, #start) == start
end

-- Hàm chính để tự động lấy tên tác giả từ dòng phụ đề
function auto_get_author(subs, sel)
    local new_sel = {}  -- Tạo bảng chứa các chỉ số dòng mới
    for i, idx in ipairs(sel) do  -- Lặp qua các chỉ số dòng đã chọn
        local line = subs[idx]  -- Lấy dòng phụ đề hiện tại
        -- Kiểm tra nếu dòng có tên tác giả theo cấu trúc đã cho
        if starts_with(line.text, "LILY:") or 
           starts_with(line.text, "HAEWON:") or 
           starts_with(line.text, "KYUJIN:") or 
           starts_with(line.text, "SULLYOON:") or 
           starts_with(line.text, "BAE:") or
           starts_with(line.text, "JIWOO:") then
           
            -- Trích xuất tên tác giả từ dòng (trước dấu ":")
            local author_name = line.text:match("^([^:]+):")
            line.actor = string.upper(author_name)  -- Đặt tên tác giả theo chữ hoa
            line.text = line.text:sub(#author_name + 2)  -- Xóa tên tác giả và dấu ":" khỏi dòng phụ đề
            subs[idx] = line  -- Cập nhật dòng phụ đề
            table.insert(new_sel, idx)  -- Thêm chỉ số dòng đã thay đổi vào bảng new_sel
        end
    end
    aegisub.set_undo_point("Auto Get Author From Sub Line")  -- Đánh dấu điểm hoàn tác
    return new_sel  -- Trả về bảng chỉ số dòng mới đã được cập nhật
end

aegisub.register_macro(script_name, script_description, auto_get_author)  -- Đăng ký macro để sử dụng trong Aegisub
