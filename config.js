window.DONATION_CONFIG = {
  donateUrl: "https://ps5-gta6-production.up.railway.app/donate",
  totalUrl: "https://ps5-gta6-production.up.railway.app/total",
  // لازم تطابق MIN_AMOUNT و MAX_AMOUNT في server/main.py
  minAmount: 2,
  maxAmount: 25,
  defaultAmount: 10,
  presetAmounts: [2, 5, 10, 25],
  goalAmount: 15000,
  // يظهر فقط إذا تعذّر الوصول لسيرفر Railway
  collectedAmount: 0,
};
