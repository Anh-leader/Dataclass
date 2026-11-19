export const fmtDate = (value: string) =>
  new Intl.DateTimeFormat('vi-VN', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Asia/Ho_Chi_Minh' }).format(new Date(value))

export const fmtDateShort = (value: string) =>
  new Intl.DateTimeFormat('vi-VN', { day: 'numeric', month: 'short', timeZone: 'Asia/Ho_Chi_Minh' }).format(new Date(value))

export const remaining = (value: string) => {
  const hours = Math.ceil((new Date(value).getTime() - Date.now()) / 3600000)
  if (hours <= 0) return 'Đã hết hạn'
  if (hours < 48) return `Còn ${hours} giờ`
  return `Còn ${Math.ceil(hours / 24)} ngày`
}

export const todayLong = () =>
  new Intl.DateTimeFormat('vi-VN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric', timeZone: 'Asia/Ho_Chi_Minh' })
    .format(new Date())
    .toLocaleUpperCase('vi-VN')
