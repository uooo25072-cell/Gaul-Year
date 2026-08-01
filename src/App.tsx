import React, { useState, useEffect } from 'react';
import {
  Gamepad2,
  ShoppingBag,
  Send,
  Code2,
  Terminal,
  Settings,
  CheckCircle2,
  XCircle,
  Clock,
  Copy,
  UserCheck,
  ShieldAlert,
  Coins,
  RefreshCw,
  FileText,
  Layers,
  Bot,
  Flame,
  Gift,
  Tv,
  ExternalLink,
  ChevronRight,
  Database,
  Sliders,
  AlertTriangle,
  Plus,
  Trash2,
  Lock,
  Unlock,
  Bell,
  BellRing,
  X,
  Check,
  AlertCircle,
  Star,
  Image as ImageIcon,
  Eye,
  User,
  Search,
  FileCheck
} from 'lucide-react';

interface BotMessage {
  id: string;
  sender: 'bot' | 'user' | 'system';
  text: string;
  timestamp: string;
  photoUrl?: string;
  buttons?: { text: string; action: string; url?: string }[][];
}

interface ToastItem {
  id: string;
  title: string;
  message: string;
  type: 'success' | 'error' | 'info';
  orderNumber?: string;
  oldStatus?: string;
  newStatus?: string;
  timestamp: string;
}

interface PackageItem {
  id: number;
  product_key: string;
  name: string;
  price_egp: number;
  is_active: number;
}

interface ProductItem {
  key: string;
  name: string;
  data_label: string;
  is_active: number;
  packages: PackageItem[];
}

interface StoreSettings {
  maintenance_mode?: string;
  maintenance_message?: string;
  vodafone_number?: string;
  vodafone_name?: string;
  binance_id?: string;
  binance_name?: string;
  ton_wallet?: string;
  ton_egp_rate?: string;
  ton_rate_updated_at?: string;
}

export default function App() {
  const [activeTab, setActiveTab] = useState<'simulator' | 'files' | 'config'>('simulator');
  const [fileList, setFileList] = useState<string[]>([]);
  const [fileContents, setFileContents] = useState<Record<string, string>>({});
  const [selectedFile, setSelectedFile] = useState<string>('main.py');
  const [envContent, setEnvContent] = useState<string>('');
  const [savedSuccess, setSavedSuccess] = useState<boolean>(false);

  // Database Driven State
  const [products, setProducts] = useState<ProductItem[]>([]);
  const [settings, setSettings] = useState<StoreSettings>({});
  const [isRefreshingRate, setIsRefreshingRate] = useState<boolean>(false);
  const [dbStats, setDbStats] = useState<any>({});
  const [allOrders, setAllOrders] = useState<any[]>([]);
  const [selectedProofOrder, setSelectedProofOrder] = useState<any | null>(null);
  const [orderSearchTerm, setOrderSearchTerm] = useState<string>('');
  const [orderFilterStatus, setOrderFilterStatus] = useState<string>('all');

  const generateProofImageUrl = (ord: any) => {
    if (!ord) return '';
    const method = (ord.payment_method || 'vodafone').toLowerCase();
    let methodTitle = 'Vodafone Cash';
    let headerBg = '#991b1b'; // red
    if (method.includes('ton')) {
      methodTitle = 'TONKeeper Wallet';
      headerBg = '#0369a1'; // cyan/blue
    } else if (method.includes('binance') || method.includes('crypto')) {
      methodTitle = 'Binance Pay / Crypto';
      headerBg = '#854d0e'; // yellow/amber
    } else if (method.includes('insta')) {
      methodTitle = 'Instapay Egypt';
      headerBg = '#3730a3'; // indigo
    }

    const svgString = `
    <svg xmlns="http://www.w3.org/2000/svg" width="480" height="320" viewBox="0 0 480 320">
      <rect width="480" height="320" rx="16" fill="#0f172a"/>
      <path d="0 0 H480 V80 H0 Z" fill="${headerBg}"/>
      <text x="240" y="38" fill="#ffffff" font-family="sans-serif" font-size="18" font-weight="bold" text-anchor="middle">إثبات تحويل - ${methodTitle}</text>
      <text x="240" y="62" fill="#e2e8f0" font-family="sans-serif" font-size="12" text-anchor="middle">حالة العملية: ✅ تحويل ناجح (SUCCESS)</text>
      
      <rect x="20" y="95" width="440" height="150" rx="12" fill="#1e293b" stroke="#334155" stroke-width="1"/>
      
      <text x="40" y="125" fill="#94a3b8" font-family="sans-serif" font-size="12">رقم الطلب:</text>
      <text x="440" y="125" fill="#f8fafc" font-family="sans-serif" font-size="13" font-weight="bold" text-anchor="end">#${ord.order_number || 'GZ-10024'}</text>
      
      <text x="40" y="150" fill="#94a3b8" font-family="sans-serif" font-size="12">اسم العميل:</text>
      <text x="440" y="150" fill="#38bdf8" font-family="sans-serif" font-size="13" font-weight="bold" text-anchor="end">${ord.full_name || 'عميل GameZone'} (@${ord.username || 'user'})</text>
      
      <text x="40" y="175" fill="#94a3b8" font-family="sans-serif" font-size="12">المبلغ المحول:</text>
      <text x="440" y="175" fill="#4ade80" font-family="sans-serif" font-size="15" font-weight="bold" text-anchor="end">${ord.price_egp || 0} EGP ${ord.ton_amount ? `(${ord.ton_amount} TON)` : ''}</text>
      
      <text x="40" y="200" fill="#94a3b8" font-family="sans-serif" font-size="12">رقم المرجع / Memo:</text>
      <text x="440" y="200" fill="#facc15" font-family="sans-serif" font-size="12" font-weight="bold" text-anchor="end">${ord.memo || ord.receipt_file_id || 'MEMO-99381'}</text>
      
      <text x="40" y="225" fill="#94a3b8" font-family="sans-serif" font-size="12">تاريخ السكرين شوت:</text>
      <text x="440" y="225" fill="#cbd5e1" font-family="sans-serif" font-size="11" text-anchor="end">${ord.created_at || '2026-08-01 03:50'}</text>
      
      <circle cx="240" cy="275" r="22" fill="#16a34a"/>
      <path d="M230 275 L237 282 L252 267" stroke="#ffffff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
      <text x="240" y="310" fill="#a7f3d0" font-family="sans-serif" font-size="10" text-anchor="middle">VERIFIED PAYMENT PROOF • GAMEZONE STORE</text>
    </svg>
    `;
    return `data:image/svg+xml;utf8,${encodeURIComponent(svgString)}`;
  };

  const fetchDbStats = async () => {
    try {
      const res = await fetch('/api/db/stats');
      const data = await res.json();
      if (data && !data.error) {
        setDbStats(data);
      }
    } catch (err) {
      console.error('Failed to fetch DB stats:', err);
    }
  };

  const fetchAllOrders = async () => {
    try {
      const res = await fetch('/api/db/orders/all');
      const data = await res.json();
      if (Array.isArray(data)) {
        setAllOrders(data);
      }
    } catch (err) {
      console.error('Failed to fetch all orders:', err);
    }
  };

  // Toast Notifications State
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const addToast = (toast: Omit<ToastItem, 'id' | 'timestamp'>) => {
    const id = Date.now().toString() + Math.random().toString(36).substring(2, 5);
    const timestamp = new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const newToast: ToastItem = { ...toast, id, timestamp };
    setToasts((prev) => [newToast, ...prev]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 6000);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const handleRefreshTonRate = async () => {
    setIsRefreshingRate(true);
    try {
      const res = await fetch('/api/db/settings/refresh_ton_rate', { method: 'POST' });
      const data = await res.json();
      if (data.rate) {
        setSettings((prev) => ({
          ...prev,
          ton_egp_rate: String(data.rate),
          ton_rate_updated_at: data.updated_at,
        }));
      }
    } catch (err) {
      console.error('Failed to refresh TON rate:', err);
    } finally {
      setIsRefreshingRate(false);
    }
  };

  // Bot Simulator State
  const [chatMessages, setChatMessages] = useState<BotMessage[]>([]);
  const [userInput, setUserInput] = useState<string>('');
  const [fsmState, setFsmState] = useState<string>('idle');
  const [currentOrder, setCurrentOrder] = useState<any>(null);
  const [myOrdersList, setMyOrdersList] = useState<any[]>([]);
  const [copiedMemo, setCopiedMemo] = useState<boolean>(false);

  // Load files, config, products, and settings from real DB backend
  const loadDbData = async () => {
    try {
      const [prodRes, settRes] = await Promise.all([
        fetch('/api/db/products'),
        fetch('/api/db/settings')
      ]);
      const prodData = await prodRes.json();
      const settData = await settRes.json();

      if (Array.isArray(prodData)) {
        setProducts(prodData);
      }
      if (settData && typeof settData === 'object' && !settData.error) {
        setSettings(settData);
      }
      fetchDbStats();
      fetchAllOrders();
    } catch (err) {
      console.error('Error fetching DB data:', err);
    }
  };

  useEffect(() => {
    fetch('/api/files')
      .then((res) => res.json())
      .then((data) => {
        if (data.files) {
          setFileList(data.files);
          setFileContents(data.fileContents || {});
        }
      })
      .catch((err) => console.error('Error loading files:', err));

    fetch('/api/config')
      .then((res) => res.json())
      .then((data) => {
        if (data.envContent) {
          setEnvContent(data.envContent);
        }
      })
      .catch((err) => console.error('Error loading config:', err));

    loadDbData();
    initBotChat();
  }, []);

  const getProductIcon = (key: string) => {
    switch (key) {
      case 'pubg':
        return Gamepad2;
      case 'freefire':
        return Flame;
      case 'googleplay':
        return Gift;
      case 'xbox':
        return Tv;
      default:
        return Gamepad2;
    }
  };

  const initBotChat = () => {
    const startMsg: BotMessage = {
      id: '1',
      sender: 'bot',
      text: '🏪 <b>مرحبًا بك في GameZone</b>\n\nالمتجر الأفضل لشحن الألعاب والبطاقات الرقمية بسرعة وأمان! ⚡️\n\nاختر الخدمة التي تريدها من الأزرار أدناه:',
      timestamp: new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' }),
      buttons: [
        [
          { text: '🎮 PUBG Mobile', action: 'prod:pubg' },
          { text: '🔥 Free Fire', action: 'prod:freefire' },
        ],
        [
          { text: '🎁 Google Play', action: 'prod:googleplay' },
          { text: '🟢 Xbox', action: 'prod:xbox' },
        ],
        [
          { text: '📦 طلباتي', action: 'user:my_orders' },
          { text: '☎️ الدعم الفني', action: 'url_support', url: 'https://t.me/vcvui' },
        ],
      ],
    };
    setChatMessages([startMsg]);
    setFsmState('main_menu');
  };

  const addMessage = (msg: BotMessage) => {
    setChatMessages((prev) => [...prev, msg]);
  };

  const handleSendMessage = (textToSend?: string) => {
    const text = textToSend || userInput;
    if (!text.trim()) return;

    const time = new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' });
    const userMsg: BotMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: text,
      timestamp: time,
    };
    addMessage(userMsg);
    setUserInput('');

    // Handle Admin command /admin
    if (text.trim() === '/admin') {
      setTimeout(() => {
        addMessage({
          id: (Date.now() + 1).toString(),
          sender: 'bot',
          text: '🛠️ <b>لوحة تحكم GameZone</b>\n\nمرحبًا بك في لوحة تحكم المتجر. يمكنك إدارة جميع العمليات والباقات والطلبات والمستخدمين من الأزرار أدناه:',
          timestamp: new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' }),
          buttons: [
            [
              { text: '📊 الإحصائيات الحية', action: 'adm:stats' },
              { text: '📦 إدارة الطلبات', action: 'adm:orders' },
            ],
            [
              { text: '🛒 المنتجات والباقات', action: 'adm:products' },
              { text: '💳 طرق الدفع', action: 'adm:payments' },
            ],
            [
              { text: '👥 المستخدمين', action: 'adm:users' },
              { text: '🛠️ وضع الصيانة', action: 'adm:toggle_maint' },
            ],
            [{ text: '⬅️ العودة للمتجر', action: 'nav:main' }],
          ],
        });
      }, 300);
      return;
    }

    if (text.trim() === '/start') {
      initBotChat();
      return;
    }

    // Handle FSM inputs
    if (fsmState === 'entering_data' && currentOrder) {
      const prodKey = currentOrder.prodKey;
      let isValid = true;
      let errorText = '';

      if (prodKey === 'pubg' || prodKey === 'freefire') {
        const isDigits = /^\d+$/.test(text.trim());
        if (!isDigits || text.trim().length < 5) {
          isValid = false;
          errorText = `❌ <b>الـ Player ID غير صحيح.</b>\n\nيرجى إرسال Player ID صحيح يحتوي على أرقام فقط (مثال: <code>123456789</code>).`;
        }
      } else if (prodKey === 'googleplay' || prodKey === 'xbox') {
        const isEmail = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/.test(text.trim());
        if (!isEmail) {
          isValid = false;
          errorText = `❌ <b>صيغة الإيميل غير صحيحة.</b>\n\nيرجى إرسال إيميل صحيح، مثال:\n<code>example@gmail.com</code>`;
        }
      }

      if (!isValid) {
        setTimeout(() => {
          addMessage({
            id: (Date.now() + 1).toString(),
            sender: 'bot',
            text: errorText,
            timestamp: new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' }),
          });
        }, 300);
        return;
      }

      // Valid input -> review order
      const updatedOrder = { ...currentOrder, customerData: text.trim() };
      setCurrentOrder(updatedOrder);

      let notice = '';
      if (prodKey === 'googleplay') {
        notice = '\n\n⚠️ <i>يرجى التأكد من صحة الإيميل، لأن التحقق الحالي يتأكد من صيغة الإيميل فقط، ويتم التأكد من الحساب أثناء تنفيذ الطلب.</i>';
      } else if (prodKey === 'xbox') {
        notice = '\n\n⚠️ <i>بطاقات Xbox هي بطاقات أمريكية (US) وتحتاج حسابًا أو متجرًا مضبوطًا على الولايات المتحدة.</i>';
      }

      setTimeout(() => {
        addMessage({
          id: (Date.now() + 1).toString(),
          sender: 'bot',
          text: `🧾 <b>مراجعة الطلب</b>\n\n🎮 <b>المنتج:</b> ${updatedOrder.prodName}\n💎 <b>الباقة:</b> ${updatedOrder.pkgName}\n🆔 <b>${updatedOrder.dataLabel}:</b> <code>${updatedOrder.customerData}</code>\n💰 <b>السعر:</b> ${updatedOrder.price} جنيه${notice}\n\n⚠️ <b>تأكد من صحة البيانات قبل تأكيد الطلب.</b>`,
          timestamp: new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' }),
          buttons: [
            [
              { text: '✅ تأكيد الطلب', action: 'order:confirm' },
              { text: '✏️ تعديل البيانات', action: 'order:edit' },
            ],
            [{ text: '❌ إلغاء', action: 'order:cancel' }],
          ],
        });
        setFsmState('confirming_order');
      }, 300);
    }
  };

  const handleButtonClick = async (action: string) => {
    const time = new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' });

    if (action === 'nav:main') {
      initBotChat();
      return;
    }

    if (action.startsWith('prod:')) {
      const key = action.split(':')[1];
      const prod = products.find((p) => p.key === key);

      if (!prod) {
        addMessage({
          id: Date.now().toString(),
          sender: 'bot',
          text: '❌ <b>المنتج غير متاح حاليًا.</b>',
          timestamp: time,
          buttons: [[{ text: '⬅️ القائمة الرئيسية', action: 'nav:main' }]],
        });
        return;
      }

      setFsmState('selecting_package');
      setCurrentOrder({
        prodKey: key,
        prodName: prod.name,
        dataLabel: prod.data_label,
      });

      const activePkgs = prod.packages.filter((pkg) => pkg.is_active === 1);
      const buttons = activePkgs.map((pkg) => [
        { text: `${pkg.name} = ${pkg.price_egp} جنيه`, action: `pkg:${pkg.id}` },
      ]);
      buttons.push([{ text: '⬅️ القائمة الرئيسية', action: 'nav:main' }]);

      addMessage({
        id: Date.now().toString(),
        sender: 'bot',
        text: `🎮 <b>اختر الباقة المناسبة لشحن ${prod.name}:</b>`,
        timestamp: time,
        buttons: buttons,
      });
      return;
    }

    if (action.startsWith('pkg:')) {
      const pkgId = parseInt(action.split(':')[1]);
      let foundPkg: PackageItem | null = null;
      let parentProd: ProductItem | null = null;

      for (const p of products) {
        const pkg = p.packages.find((k) => k.id === pkgId);
        if (pkg) {
          foundPkg = pkg;
          parentProd = p;
          break;
        }
      }

      if (foundPkg && parentProd) {
        const updated = {
          prodKey: parentProd.key,
          prodName: parentProd.name,
          dataLabel: parentProd.data_label,
          pkgId: foundPkg.id,
          pkgName: foundPkg.name,
          price: foundPkg.price_egp,
        };
        setCurrentOrder(updated);
        setFsmState('entering_data');

        let prompt = `📥 <b>يرجى إرسال الـ ${updated.dataLabel} الخاص بك:</b>\n\n💡 مثال: <code>123456789</code>`;
        if (updated.prodKey === 'googleplay') {
          prompt = `📥 <b>يرجى إرسال الإيميل المرتبط بحساب Google Play:</b>\n\n💡 مثال: <code>example@gmail.com</code>\n\n⚠️ <b>ملاحظة:</b> تحقق من صحة الإيميل، لأن التحقق الحالي يتأكد من صيغة الإيميل فقط، ويتم التأكد من الحساب أثناء تنفيذ الطلب.`;
        } else if (updated.prodKey === 'xbox') {
          prompt = `📥 <b>يرجى إرسال الإيميل المرتبط بحساب Xbox:</b>\n\n💡 مثال: <code>example@outlook.com</code>\n\n⚠️ <b>تنبيه هام:</b> بطاقات Xbox هي بطاقات أمريكية (US) وتحتاج حسابًا أو متجرًا مضبوطًا على الولايات المتحدة.`;
        }

        addMessage({
          id: Date.now().toString(),
          sender: 'bot',
          text: prompt,
          timestamp: time,
        });
      }
      return;
    }

    if (action === 'order:confirm') {
      try {
        const res = await fetch('/api/db/orders', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: 123456789,
            product_key: currentOrder.prodKey,
            package_id: currentOrder.pkgId,
            customer_data: currentOrder.customerData,
            payment_method: 'vodafone',
          }),
        });
        const createdOrder = await res.json();

        if (createdOrder && createdOrder.order_number) {
          const finalOrd = {
            ...currentOrder,
            id: createdOrder.id,
            orderNumber: createdOrder.order_number,
            memo: createdOrder.memo || `GAMEZONE-${createdOrder.order_number}`,
            tonAmount: createdOrder.ton_amount || (currentOrder.price / parseFloat(settings.ton_egp_rate || '120.0')).toFixed(2),
            status: createdOrder.status,
            createdAt: createdOrder.created_at,
          };
          setCurrentOrder(finalOrd);

          addMessage({
            id: Date.now().toString(),
            sender: 'bot',
            text: `✅ <b>تم إنشاء طلبك وحفظه برقم:</b> <code>${finalOrd.orderNumber}</code>\n\n💳 <b>اختر طريقة الدفع المناسبة لك:</b>\n⏱️ <b>مهلة الدفع:</b> 20 دقيقة`,
            timestamp: time,
            buttons: [
              [{ text: '📱 Vodafone Cash', action: 'pay:vodafone' }],
              [{ text: '🟡 Binance ID', action: 'pay:binance' }],
              [{ text: '🪙 TONKeeper', action: 'pay:ton' }],
              [{ text: '❌ إلغاء الطلب', action: 'order:cancel' }],
            ],
          });
        }
      } catch (err) {
        console.error('Failed to create order in DB:', err);
      }
      return;
    }

    if (action === 'pay:vodafone') {
      const vNum = settings.vodafone_number || '01557535435';
      const vName = settings.vodafone_name || 'Ahmed';

      addMessage({
        id: Date.now().toString(),
        sender: 'bot',
        text: `📱 <b>الدفع عبر Vodafone Cash</b>\n\n💰 <b>المبلغ المطلوب:</b> ${currentOrder?.price} جنيه\n\n📞 <b>رقم التحويل:</b>\n<code>${vNum}</code>\n\n👤 <b>الاسم المسجل:</b>\n<b>${vName}</b>\n\n⚠️ <b>حوّل المبلغ المطلوب بدقة.</b>\n\nبعد إتمام التحويل، اضغط على <b>✅ تم الدفع</b> لإرسال صورة الإثبات.`,
        timestamp: time,
        buttons: [
          [{ text: '✅ تم الدفع', action: 'pay:upload_proof' }],
          [{ text: '❌ إلغاء الطلب', action: 'order:cancel' }],
        ],
      });
      return;
    }

    if (action === 'pay:binance') {
      const bId = settings.binance_id || '1097135483';
      const bName = settings.binance_name || 'Ahmed10';

      addMessage({
        id: Date.now().toString(),
        sender: 'bot',
        text: `🟡 <b>الدفع عبر Binance Pay / ID</b>\n\n💰 <b>المبلغ المطلوب:</b> ${currentOrder?.price} جنيه\n\n🆔 <b>Binance Pay ID:</b>\n<code>${bId}</code>\n\n👤 <b>الاسم المسجل:</b>\n<b>${bName}</b>\n\n⚠️ <b>حوّل المبلغ المطلوب بدقة.</b>\n\nبعد إتمام التحويل، اضغط على <b>✅ تم الدفع</b> لإرسال صورة الإثبات.`,
        timestamp: time,
        buttons: [
          [{ text: '✅ تم الدفع', action: 'pay:upload_proof' }],
          [{ text: '❌ إلغاء الطلب', action: 'order:cancel' }],
        ],
      });
      return;
    }

    if (action === 'pay:ton') {
      const wallet = settings.ton_wallet || 'UQAerMfM0XruMQmynNMjIuKP7zu4AeMrVlUBRJgtxARyLq_H';
      const memo = currentOrder?.memo || 'GZ123456';
      const tonAmount = currentOrder?.tonAmount || 0;
      const nanotons = Math.round(parseFloat(tonAmount || '0') * 1_000_000_000);
      const tonkeeperUrl = `https://app.tonkeeper.com/transfer/${wallet}?amount=${nanotons}&text=${memo}`;

      addMessage({
        id: Date.now().toString(),
        sender: 'bot',
        text: `🪙 <b>الدفع عبر شبكة TON (من أي محفظة)</b>\n\n💰 <b>المبلغ المطلوب:</b>\n<code>${tonAmount} TON</code>\n\n👛 <b>عنوان المحفظة (Address):</b>\n<code>${wallet}</code>\n\n📝 <b>Memo (ملاحظة التحويل):</b>\n<code>${memo}</code>\n\nℹ️ <b>تعليمات التحويل:</b>\n• يمكنك التحويل من <b>أي محفظة TON</b> (مثل: TONKeeper, Telegram Wallet, OKX, MyTonWallet, Tonhub وغيرها).\n• قم بنسخ <b>عنوان المحفظة</b> و <b>المبلغ</b> و <b>Memo</b> بدقة.\n⚠️ <b>تنبيه هام:</b> يرجى عدم نسيان إدخال الـ <b>Memo</b> أثناء التحويل.\n\nبعد إتمام التحويل:`,
        timestamp: time,
        buttons: [
          [{ text: '💎 فتح محفظة TONKeeper للدفع', action: 'url_tonkeeper', url: tonkeeperUrl }],
          [{ text: '📋 نسخ عنوان المحفظة', action: 'copy_wallet' }],
          [{ text: '📋 نسخ الـ Memo', action: 'copy_memo' }],
          [{ text: '⚡ التحقق التلقائي من الشبكة', action: 'pay:check_ton' }],
          [{ text: '📸 إرسال صورة إثبات التحويل (Screenshot)', action: 'pay:upload_proof' }],
          [{ text: '❌ إلغاء الطلب', action: 'order:cancel' }],
        ],
      });
      return;
    }

    if (action === 'copy_wallet') {
      const wallet = settings.ton_wallet || 'UQAerMfM0XruMQmynNMjIuKP7zu4AeMrVlUBRJgtxARyLq_H';
      navigator.clipboard.writeText(wallet);
      addMessage({
        id: Date.now().toString(),
        sender: 'bot',
        text: `📋 <b>تم نسخ عنوان المحفظة بنجاح:</b>\n<code>${wallet}</code>`,
        timestamp: time,
      });
      return;
    }

    if (action === 'copy_memo') {
      if (currentOrder?.memo) {
        navigator.clipboard.writeText(currentOrder.memo);
        setCopiedMemo(true);
        setTimeout(() => setCopiedMemo(false), 2000);
        addMessage({
          id: Date.now().toString(),
          sender: 'bot',
          text: `📋 <b>تم نسخ الـ Memo بنجاح:</b>\n<code>${currentOrder.memo}</code>`,
          timestamp: time,
        });
      }
      return;
    }

    if (action === 'pay:upload_proof') {
      addMessage({
        id: Date.now().toString(),
        sender: 'bot',
        text: `📸 <b>يرجى إرسال صورة إثبات التحويل (Screenshot/Receipt):</b>\n\nتأكد من وضوح قيمة المبلغ ورقم العملية وحالة التحويل بالصورة.`,
        timestamp: time,
        buttons: [
          [{ text: '📤 رفع وتأكيد إرسال صورة الإثبات', action: 'submit_proof_confirm' }],
          [{ text: '❌ إلغاء الطلب', action: 'order:cancel' }],
        ],
      });
      setFsmState('waiting_for_proof');
      return;
    }

    if (action === 'submit_proof_confirm') {
      if (currentOrder?.orderNumber) {
        await fetch('/api/db/orders/receipt', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            order_number: currentOrder.orderNumber,
            receipt_file_id: 'receipt_simulated_' + Date.now(),
          }),
        });
      }

      // Add user message simulating image submission
      addMessage({
        id: (Date.now() - 10).toString(),
        sender: 'user',
        text: `📷 <i>[تم إرفاق صورة إثبات التحويل للطلب #${currentOrder?.orderNumber || ''}]</i>`,
        timestamp: time,
      });

      addMessage({
        id: Date.now().toString(),
        sender: 'bot',
        text: `🔍 <b>جاري مراجعة الدفع لطلبك #${currentOrder?.orderNumber}!</b>\n\nتم استلام صورة إثبات التحويل بنجاح وإرسالها إلى الأدمن للمراجعة والتأكيد.\nسنقوم بتحديث حالة الطلب فور التأكد.`,
        timestamp: time,
        buttons: [[{ text: '⬅️ القائمة الرئيسية', action: 'nav:main' }]],
      });

      addToast({
        title: '📸 تم رفع صورة الإثبات بنجاح',
        message: `تم إرسال صورة إثبات التحويل للطلب #${currentOrder?.orderNumber} إلى الأدمن للمراجعة.`,
        type: 'info',
        orderNumber: currentOrder?.orderNumber,
        oldStatus: 'في انتظار الدفع',
        newStatus: 'قيد المراجعة',
      });

      setFsmState('idle');
      return;
    }

    if (action === 'pay:check_ton') {
      if (!currentOrder?.orderNumber) return;

      try {
        const res = await fetch('/api/db/orders/check_ton', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ order_number: currentOrder.orderNumber }),
        });
        const result = await res.json();

        if (result.success) {
          addMessage({
            id: Date.now().toString(),
            sender: 'bot',
            text: `✅ <b>تم التحقق من وصول دفعتك بنجاح عبر شبكة TON!</b>\n\n🧾 <b>رقم الطلب:</b> <code>${currentOrder.orderNumber}</code>\n🔗 <b>Tx Hash:</b> <code>${result.tx_hash || 'على الشبكة'}</code>\n📦 طلبك الآن ⚙️ <b>قيد التنفيذ</b> وسيتم شحنه يدويًا.`,
            timestamp: time,
            buttons: [[{ text: '⬅️ القائمة الرئيسية', action: 'nav:main' }]],
          });
        } else {
          const wallet = settings.ton_wallet || 'UQAerMfM0XruMQmynNMjIuKP7zu4AeMrVlUBRJgtxARyLq_H';
          const memo = currentOrder?.memo || 'GZ123456';
          const tonAmount = currentOrder?.tonAmount || 0;
          const nanotons = Math.round(parseFloat(tonAmount || '0') * 1_000_000_000);
          const tonkeeperUrl = `https://app.tonkeeper.com/transfer/${wallet}?amount=${nanotons}&text=${memo}`;

          addMessage({
            id: Date.now().toString(),
            sender: 'bot',
            text: `❌ <b>لم تصل الفلوس إلى المحفظة بعد.</b>\n\nيرجى التأكد من إتمام عملية التحويل عبر TONKeeper كالتالي:\n1️⃣ فتح المحفظة وإكمال التحويل.\n2️⃣ التأكد من إرفاق الـ Memo المطلوب: <code>${memo}</code>.\n3️⃣ الانتظار لعدة ثوانٍ ثم الضغط على <b>✅ تم الدفع (التحقق من الدفع)</b> للمحاولة مرة أخرى.`,
            timestamp: time,
            buttons: [
              [{ text: '💎 فتح محفظة TONKeeper للدفع تلقائيًا', action: 'url_tonkeeper', url: tonkeeperUrl }],
              [{ text: '📋 نسخ الـ Memo', action: 'copy_memo' }],
              [{ text: '✅ تم الدفع (التحقق من الدفع)', action: 'pay:check_ton' }],
              [{ text: '❌ إلغاء', action: 'order:cancel' }],
            ],
          });
        }
      } catch (err) {
        console.error("Error checking TON payment:", err);
      }
      return;
    }

    if (action === 'user:my_orders') {
      try {
        const res = await fetch('/api/db/orders/user/123456789');
        const userOrders = await res.json();

        if (!Array.isArray(userOrders) || userOrders.length === 0) {
          addMessage({
            id: Date.now().toString(),
            sender: 'bot',
            text: '📦 <b>لا توجد لديك طلبات سابقة في قاعدة البيانات حتى الآن.</b>',
            timestamp: time,
            buttons: [[{ text: '⬅️ القائمة الرئيسية', action: 'nav:main' }]],
          });
        } else {
          const orderButtons = userOrders.slice(0, 10).map((ord) => [
            {
              text: `📦 #${ord.order_number} - ${ord.product_name} (${ord.price_egp}ج)`,
              action: `view_ord:${ord.order_number}`,
            },
          ]);
          orderButtons.push([{ text: '⬅️ القائمة الرئيسية', action: 'nav:main' }]);

          addMessage({
            id: Date.now().toString(),
            sender: 'bot',
            text: `📦 <b>قائمة طلباتك الحقيقية من قاعدة البيانات (${userOrders.length} طلب):</b>\n\nاضغط على أي طلب لمعاينة تفاصيله:`,
            timestamp: time,
            buttons: orderButtons,
          });
        }
      } catch (err) {
        console.error('Failed to fetch user orders:', err);
      }
      return;
    }

    if (action === 'adm:orders') {
      try {
        const res = await fetch('/api/db/orders/all');
        const orders = await res.json();

        if (!Array.isArray(orders) || orders.length === 0) {
          addMessage({
            id: Date.now().toString(),
            sender: 'bot',
            text: '📦 <b>لا توجد أي طلبات في قاعدة البيانات حاليًا.</b>',
            timestamp: time,
            buttons: [[{ text: '⬅️ لوحة تحكم الأدمن', action: '/admin' }]],
          });
        } else {
          const orderButtons = orders.slice(0, 10).map((ord) => {
            const statusBadge =
              ord.status === 'completed' ? '✅' :
              ord.status === 'rejected' ? '❌' :
              ord.status === 'processing' ? '⚙️' : '🔍';
            return [
              {
                text: `${statusBadge} #${ord.order_number} - ${ord.product_name} (${ord.price_egp}ج)`,
                action: `adm_view_ord:${ord.order_number}`,
              },
            ];
          });
          orderButtons.push([{ text: '⬅️ لوحة تحكم الأدمن', action: '/admin' }]);

          addMessage({
            id: Date.now().toString(),
            sender: 'bot',
            text: `📦 <b>إدارة جميع طلبات المتجر في قاعدة البيانات (${orders.length} طلب):</b>\n\nاضغط على أي طلب لمراجعة بياناته واعتماده أو رفضه:`,
            timestamp: time,
            buttons: orderButtons,
          });
        }
      } catch (err) {
        console.error('Failed to fetch admin orders:', err);
      }
      return;
    }

    if (action.startsWith('adm_zoom_proof:')) {
      const orderNum = action.split(':')[1];
      const ord = allOrders.find((o) => String(o.order_number) === String(orderNum));
      if (ord) {
        setSelectedProofOrder(ord);
        addToast({
          title: '🖼️ تم فتح معاينة الإثبات',
          message: `تم فتح نافذة الفحص المكبرة لصورة إثبات الدفع للطلب #${orderNum}`,
          type: 'info',
        });
      }
      return;
    }

    if (action.startsWith('adm_view_ord:') || action.startsWith('view_ord:')) {
      const orderNum = action.split(':')[1];
      try {
        const res = await fetch('/api/db/orders/all');
        const orders = await res.json();
        const ord = Array.isArray(orders) ? orders.find((o) => String(o.order_number) === String(orderNum)) : null;

        if (ord) {
          const statusTxt =
            ord.status === 'completed' ? '✅ مكتمل' :
            ord.status === 'rejected' ? '❌ مرفوض' :
            ord.status === 'processing' ? '⚙️ قيد التنفيذ' :
            ord.status === 'payment_review' ? '🔍 قيد المراجعة' : '⏳ في انتظار الدفع';

          const proofImgUrl = generateProofImageUrl(ord);

          addMessage({
            id: Date.now().toString(),
            sender: 'bot',
            photoUrl: proofImgUrl,
            text: `📦 <b>تفاصيل الطلب ومقدم الطلب #${ord.order_number}</b>\n\n👤 <b>معلومات العميل (مقدم الطلب):</b>\n• <b>الاسم الكامل:</b> ${ord.full_name || 'عميل GameZone'}\n• <b>اليوزر نيم:</b> @${ord.username || 'بدون_يوزر'}\n• <b>Telegram ID:</b> <code>${ord.user_id || ord.telegram_id || '102938475'}</code>\n• <b>حالة الحساب:</b> ${ord.is_banned ? '🔴 محظور' : '🟢 حساب نشط'}\n\n🎮 <b>تفاصيل الطلب والشحن:</b>\n• <b>المنتج والباقة:</b> ${ord.product_name} - ${ord.package_name}\n• <b>المبلغ المطلوب:</b> ${ord.price_egp} EGP ${ord.ton_amount ? `(${ord.ton_amount} TON)` : ''}\n• <b>طريقة الدفع:</b> ${ord.payment_method?.toUpperCase()}\n• <b>الـ Memo / المرجع:</b> <code>${ord.memo || ord.receipt_file_id || 'GZ-PROOF-9931'}</code>\n• <b>بيانات العميل باللعبة:</b> <code>${ord.customer_data}</code>\n• <b>التقييم:</b> ${ord.rating ? `⭐ ${ord.rating}/5 (${ord.rating_comment || 'ممتاز'})` : 'لم يتم التقييم بعد'}\n• <b>الحالة الحالية:</b> ${statusTxt}\n• <b>تاريخ الطلب:</b> ${ord.created_at}\n\n📸 <b>صورة إثبات الدفع (Screenshot) موصحة أعلى الرسالة ⬆️</b>`,
            timestamp: time,
            buttons: [
              [{ text: '🖼️ فتح صورة الإثبات في نافذة الفحص المكبرة', action: `adm_zoom_proof:${ord.order_number}` }],
              [
                { text: '✅ اعتماد مكتمل', action: `adm_approve:${ord.order_number}` },
                { text: '❌ رفض الطلب', action: `adm_reject:${ord.order_number}` },
              ],
              [{ text: '⬅️ إدارة الطلبات', action: 'adm:orders' }],
            ],
          });
        }
      } catch (err) {
        console.error('Failed to fetch order details:', err);
      }
      return;
    }

    if (action.startsWith('adm_approve:')) {
      const orderNum = action.split(':')[1];
      try {
        const res = await fetch('/api/db/orders/status', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ order_number: orderNum, status: 'completed' }),
        });
        const data = await res.json();
        if (data.status === 'ok') {
          fetchDbStats();
          fetchAllOrders();
          addToast({
            title: '✅ تم اكتمال الطلب بنجاح',
            message: `تم تحديث حالة الطلب #${orderNum} من "قيد المراجعة" إلى "مكتمل".`,
            type: 'success',
            orderNumber: orderNum,
            oldStatus: 'قيد المراجعة',
            newStatus: 'مكتمل',
          });

          addMessage({
            id: Date.now().toString(),
            sender: 'bot',
            text: `✅ <b>تم تحديث حالة الطلب #${orderNum} إلى "مكتمل" بنجاح في قاعدة البيانات!</b>\n\n🎉 <b>رسالة التقييم التلقائية للعميل:</b>\n"كيف كانت تجربتك في شراء هذا الطلب؟ يرجى تقييم الخدمة لمساعدتنا في تحسين المتجر:"`,
            timestamp: time,
            buttons: [
              [{ text: '⭐ ⭐ ⭐ ⭐ ⭐ (ممتاز 5/5)', action: `rate_ord:${orderNum}:5` }],
              [
                { text: '⭐ ⭐ ⭐ ⭐ (جيد 4/5)', action: `rate_ord:${orderNum}:4` },
                { text: '⭐ ⭐ ⭐ (مقبول 3/5)', action: `rate_ord:${orderNum}:3` },
              ],
              [
                { text: '⭐ ⭐ (سيئ 2/5)', action: `rate_ord:${orderNum}:2` },
                { text: '⭐ (سيئ جداً 1/5)', action: `rate_ord:${orderNum}:1` },
              ],
              [{ text: '⬅️ قائمة الطلبات', action: 'adm:orders' }],
            ],
          });
        }
      } catch (err) {
        console.error('Failed to update status:', err);
      }
      return;
    }

    if (action.startsWith('rate_ord:')) {
      const parts = action.split(':');
      const orderNum = parts[1];
      const stars = parseInt(parts[2], 10);

      try {
        const res = await fetch('/api/db/orders/rate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ order_number: orderNum, rating: stars }),
        });
        const data = await res.json();
        if (data.status === 'ok') {
          fetchDbStats();
          addToast({
            title: '⭐ تم تسجيل التقييم بنجاح',
            message: `شكراً لك! تم تسجيل تقييمك (${stars}/5) للطلب #${orderNum} في قاعدة البيانات.`,
            type: 'success',
            orderNumber: orderNum,
          });

          addMessage({
            id: Date.now().toString(),
            sender: 'bot',
            text: `⭐ <b>شكرًا جزيلاً لك على تقييمك (${stars}/5)!</b>\n\nنقدر رأيك الملاحظ جدًا وسعداء بخدمتك دائمًا ❤️\nتم تحديث متوسط التقييمات في لوحة تحكم الأدمن.`,
            timestamp: time,
            buttons: [[{ text: '⬅️ القائمة الرئيسية', action: 'nav:main' }]],
          });
        }
      } catch (err) {
        console.error('Failed to save rating:', err);
      }
      return;
    }

    if (action.startsWith('adm_reject:')) {
      const orderNum = action.split(':')[1];
      try {
        const res = await fetch('/api/db/orders/status', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ order_number: orderNum, status: 'rejected', reason: 'مرفوض من الأدمن' }),
        });
        const data = await res.json();
        if (data.status === 'ok') {
          fetchDbStats();
          fetchAllOrders();
          addToast({
            title: '❌ تم رفض الطلب',
            message: `تم تحديث حالة الطلب #${orderNum} من "قيد المراجعة" إلى "مرفوض".`,
            type: 'error',
            orderNumber: orderNum,
            oldStatus: 'قيد المراجعة',
            newStatus: 'مرفوض',
          });

          addMessage({
            id: Date.now().toString(),
            sender: 'bot',
            text: `❌ <b>تم تحديث حالة الطلب #${orderNum} إلى "مرفوض" في قاعدة البيانات.</b>\n\n🔔 تم إرسال تنبيه (Toast Notification) في واجهة المحاكي.`,
            timestamp: time,
            buttons: [[{ text: '⬅️ قائمة الطلبات', action: 'adm:orders' }]],
          });
        }
      } catch (err) {
        console.error('Failed to update status:', err);
      }
      return;
    }

    if (action === 'adm:stats') {
      try {
        const res = await fetch('/api/db/stats');
        const stats = await res.json();

        addMessage({
          id: Date.now().toString(),
          sender: 'bot',
          text: `📊 <b>إحصائيات متجر GameZone الحقيقية (من SQLite)</b>\n\n👥 <b>إجمالي المستخدمين:</b> ${stats.total_users || 0}\n📦 <b>إجمالي الطلبات:</b> ${stats.total_orders || 0}\n\n⏳ <b>في انتظار الدفع:</b> ${stats.pending_payment || 0}\n🔍 <b>قيد المراجعة:</b> ${stats.payment_review || 0}\n⚙️ <b>قيد التنفيذ:</b> ${stats.processing || 0}\n✅ <b>الطلبات المكتملة:</b> ${stats.completed || 0}\n❌ <b>الطلبات المرفوضة:</b> ${stats.rejected || 0}\n\n⭐ <b>متوسط تقييمات العملاء:</b> 🌟 ${stats.avg_rating || 0.0} / 5.0 (${stats.total_ratings || 0} تقييم)\n\n💰 <b>إجمالي المبيعات:</b> ${stats.total_sales || 0} جنيه\n📈 <b>مبيعات اليوم:</b> ${stats.today_sales || 0} جنيه`,
          timestamp: time,
          buttons: [[{ text: '⬅️ لوحة تحكم الأدمن', action: '/admin' }]],
        });
      } catch (err) {
        console.error('Failed to fetch stats:', err);
      }
      return;
    }

    if (action === 'adm:toggle_maint') {
      const currentMode = settings.maintenance_mode === '1';
      const newMode = currentMode ? '0' : '1';

      await fetch('/api/db/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: 'maintenance_mode', value: newMode }),
      });

      setSettings((prev) => ({ ...prev, maintenance_mode: newMode }));

      addMessage({
        id: Date.now().toString(),
        sender: 'bot',
        text: newMode === '1'
          ? '🔴 <b>تم تفعيل وضع الصيانة في قاعدة البيانات. المتجر مغلق الآن للمستخدمين.</b>'
          : '🟢 <b>تم إيقاف وضع الصيانة في قاعدة البيانات. المتجر يعمل بشكل طبيعي الآن.</b>',
        timestamp: time,
        buttons: [[{ text: '⬅️ لوحة تحكم الأدمن', action: '/admin' }]],
      });
      return;
    }

    if (action === 'adm:payments') {
      const currentRate = settings.ton_egp_rate || '120.0';
      const lastUpdate = settings.ton_rate_updated_at || 'غير محدد';
      addMessage({
        id: Date.now().toString(),
        sender: 'bot',
        text: `💳 <b>إدارة بيانات وطرق الدفع</b>\n\n📊 <b>سعر صرف TON الحالي:</b> <code>${currentRate} EGP</code>\n🕒 <b>آخر تحديث للسعر:</b> <code>${lastUpdate}</code>\n\nاختر وسيلة الدفع لتعديل بياناتها أو اضغط تحديث السعر لجلب سعر السوق المباشر:`,
        timestamp: time,
        buttons: [
          [{ text: '📱 Vodafone Cash', action: 'adm_pay_edit:vodafone' }],
          [{ text: '🟡 Binance ID', action: 'adm_pay_edit:binance' }],
          [{ text: '🪙 محفظة TONKeeper', action: 'adm_pay_edit:ton' }],
          [{ text: '🔄 تحديث سعر TON/EGP فورًا', action: 'adm:refresh_ton' }],
          [{ text: '⬅️ لوحة تحكم الأدمن', action: '/admin' }],
        ],
      });
      return;
    }

    if (action === 'adm:refresh_ton') {
      try {
        const res = await fetch('/api/db/settings/refresh_ton_rate', { method: 'POST' });
        const data = await res.json();
        const newRate = data.rate || settings.ton_egp_rate || '120.0';
        const newTime = data.updated_at || 'الآن';

        setSettings((prev) => ({
          ...prev,
          ton_egp_rate: String(newRate),
          ton_rate_updated_at: newTime,
        }));

        addMessage({
          id: Date.now().toString(),
          sender: 'bot',
          text: `✅ <b>تم تحديث سعر صرف TON بنجاح من API!</b>\n\n📊 <b>السعر الجديد:</b> <code>${newRate} EGP</code>\n🕒 <b>وقت التحديث:</b> <code>${newTime}</code>`,
          timestamp: time,
          buttons: [[{ text: '⬅️ طرق الدفع', action: 'adm:payments' }]],
        });
      } catch (err) {
        console.error('Failed to refresh TON rate:', err);
      }
      return;
    }

    if (action === 'order:cancel') {
      addMessage({
        id: Date.now().toString(),
        sender: 'bot',
        text: '❌ <b>تم إلغاء العملية.</b>',
        timestamp: time,
        buttons: [[{ text: '⬅️ القائمة الرئيسية', action: 'nav:main' }]],
      });
      setFsmState('idle');
      return;
    }
  };

  const handleSaveEnv = () => {
    fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ envContent }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          setSavedSuccess(true);
          setTimeout(() => setSavedSuccess(false), 3000);
        }
      });
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans dir-rtl relative">
      {/* Floating Toast Notifications Overlay */}
      <div className="fixed top-5 left-5 z-[100] flex flex-col gap-3 max-w-sm w-full pointer-events-none dir-rtl">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`pointer-events-auto p-4 rounded-2xl shadow-2xl border backdrop-blur-xl transition-all duration-300 flex items-start gap-3 relative animate-in fade-in slide-in-from-top-4 ${
              t.type === 'success'
                ? 'bg-slate-900/95 border-emerald-500/60 text-slate-100 shadow-emerald-950/50'
                : t.type === 'error'
                ? 'bg-slate-900/95 border-rose-500/60 text-slate-100 shadow-rose-950/50'
                : 'bg-slate-900/95 border-amber-500/60 text-slate-100 shadow-amber-950/50'
            }`}
          >
            <div
              className={`p-2 rounded-xl shrink-0 mt-0.5 ${
                t.type === 'success'
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : t.type === 'error'
                  ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                  : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
              }`}
            >
              {t.type === 'success' ? (
                <CheckCircle2 className="w-5 h-5" />
              ) : t.type === 'error' ? (
                <XCircle className="w-5 h-5" />
              ) : (
                <Bell className="w-5 h-5" />
              )}
            </div>

            <div className="flex-1 space-y-1">
              <div className="flex items-center justify-between gap-2">
                <h4 className="font-bold text-xs flex items-center gap-1 text-slate-100">
                  <span>{t.title}</span>
                </h4>
                <span className="text-[10px] text-slate-400 font-mono shrink-0">{t.timestamp}</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">{t.message}</p>

              {t.orderNumber && (
                <div className="flex items-center gap-2 pt-1.5 border-t border-slate-800/80">
                  <span className="text-[10px] px-2 py-0.5 rounded-md bg-slate-800 border border-slate-700 text-amber-400 font-mono font-bold">
                    #{t.orderNumber}
                  </span>
                  {t.oldStatus && t.newStatus && (
                    <span className="text-[10px] text-slate-400 flex items-center gap-1">
                      <span className="line-through text-slate-500">{t.oldStatus}</span>
                      <span>➔</span>
                      <span
                        className={
                          t.type === 'success'
                            ? 'text-emerald-400 font-bold'
                            : 'text-rose-400 font-bold'
                        }
                      >
                        {t.newStatus}
                      </span>
                    </span>
                  )}
                </div>
              )}
            </div>

            <button
              onClick={() => removeToast(t.id)}
              className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition shrink-0"
              title="إغلاق التنبيه"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>

      {/* Top Header Banner */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur px-6 py-4 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 to-orange-600 flex items-center justify-center shadow-lg shadow-amber-500/20">
            <Gamepad2 className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-amber-400 to-orange-500">
              GameZone Bot Console
            </h1>
            <p className="text-xs text-slate-400">Python 3.12+ • aiogram 3.x • SQLite Persisted • APScheduler</p>
          </div>
        </div>

        {/* Top Right Navigation Tabs */}
        <div className="flex items-center bg-slate-800/80 p-1.5 rounded-xl border border-slate-700/50">
          <button
            onClick={() => setActiveTab('simulator')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'simulator'
                ? 'bg-amber-500 text-slate-950 shadow-md font-semibold'
                : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
            }`}
          >
            <Bot className="w-4 h-4" />
            <span>محاكي تليجرام</span>
          </button>
          <button
            onClick={() => setActiveTab('files')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'files'
                ? 'bg-amber-500 text-slate-950 shadow-md font-semibold'
                : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
            }`}
          >
            <Code2 className="w-4 h-4" />
            <span>ملفات المشروع ({fileList.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('config')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'config'
                ? 'bg-amber-500 text-slate-950 shadow-md font-semibold'
                : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
            }`}
          >
            <Settings className="w-4 h-4" />
            <span>إعدادات .env</span>
          </button>
        </div>
      </header>

      {/* Main Container Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 flex flex-col gap-6">
        {/* Tab 1: Interactive Telegram Bot Simulator */}
        {activeTab === 'simulator' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Telegram Phone Viewport */}
            <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden flex flex-col h-[750px]">
              {/* Telegram App Header */}
              <div className="bg-slate-850 px-5 py-3.5 border-b border-slate-800 flex items-center justify-between bg-slate-800/60 backdrop-blur">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-amber-500 to-orange-500 flex items-center justify-center text-white font-bold shadow">
                    GZ
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-slate-100 flex items-center gap-1.5">
                      <span>GameZone Store</span>
                      <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    </h3>
                    <p className="text-xs text-slate-400">bot • aiogram 3.x engine</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleSendMessage('/admin')}
                    className="px-3 py-1.5 bg-rose-500/15 border border-rose-500/40 text-rose-300 hover:bg-rose-500/25 text-xs rounded-lg font-bold transition shadow-sm"
                  >
                    🔐 /admin
                  </button>
                  <button
                    onClick={initBotChat}
                    className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition"
                    title="إعادة تشغيل البوت"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Chat Content Messages Area */}
              <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-slate-950/60 custom-scrollbar">
                {copiedMemo && (
                  <div className="bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs px-3 py-2 rounded-lg text-center font-medium animate-bounce">
                    📋 تم نسخ Memo التحويل إلى الحافظة!
                  </div>
                )}
                {chatMessages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex flex-col ${
                      msg.sender === 'user' ? 'items-end' : 'items-start'
                    }`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                        msg.sender === 'user'
                          ? 'bg-amber-600 text-white rounded-br-xs shadow-md'
                          : 'bg-slate-800 text-slate-100 border border-slate-700/60 rounded-bl-xs shadow'
                      }`}
                    >
                      <div
                        dangerouslySetInnerHTML={{ __html: msg.text.replace(/\n/g, '<br/>') }}
                      />
                      <div
                        className={`text-[10px] mt-1.5 text-left ${
                          msg.sender === 'user' ? 'text-amber-200' : 'text-slate-400'
                        }`}
                      >
                        {msg.timestamp}
                      </div>
                    </div>

                    {/* Inline Buttons Keyboard Rendering */}
                    {msg.buttons && msg.buttons.length > 0 && (
                      <div className="w-full max-w-[85%] mt-2 space-y-1.5">
                        {msg.buttons.map((row, rIdx) => (
                          <div key={rIdx} className="grid grid-cols-2 gap-1.5">
                            {row.map((btn, bIdx) => {
                              const isAdminBtn =
                                btn.action.startsWith('adm') ||
                                btn.action.startsWith('/admin') ||
                                btn.action.includes('admin') ||
                                btn.text.includes('أدمن') ||
                                btn.text.includes('الأدمن');

                              if (btn.url) {
                                return (
                                  <a
                                    key={bIdx}
                                    href={btn.url}
                                    target="_blank"
                                    rel="noreferrer"
                                    className={`${
                                      row.length === 1 ? 'col-span-2' : 'col-span-1'
                                    } ${
                                      isAdminBtn
                                        ? 'bg-rose-900/90 hover:bg-rose-800 border-rose-500/50 text-rose-200 shadow-rose-950/40'
                                        : 'bg-emerald-900/90 hover:bg-emerald-800 border-emerald-500/50 text-emerald-200 shadow-emerald-950/40'
                                    } border text-xs py-2.5 px-3 rounded-xl font-bold flex items-center justify-center gap-1.5 shadow-md transition-all active:scale-[0.98]`}
                                  >
                                    <span>{btn.text}</span>
                                    <ExternalLink className="w-3.5 h-3.5" />
                                  </a>
                                );
                              }

                              return (
                                <button
                                  key={bIdx}
                                  onClick={() =>
                                    btn.action.startsWith('/')
                                      ? handleSendMessage(btn.action)
                                      : handleButtonClick(btn.action)
                                  }
                                  className={`${
                                    row.length === 1 ? 'col-span-2' : 'col-span-1'
                                  } ${
                                    isAdminBtn
                                      ? 'bg-rose-950/80 hover:bg-rose-900 border-rose-500/50 text-rose-200 hover:text-white shadow-rose-950/40'
                                      : 'bg-emerald-950/80 hover:bg-emerald-900 border-emerald-500/50 text-emerald-200 hover:text-white shadow-emerald-950/40'
                                  } border active:scale-[0.98] text-xs py-2.5 px-3 rounded-xl font-medium text-center shadow-md transition-all flex items-center justify-center gap-1.5`}
                                >
                                  {btn.text}
                                </button>
                              );
                            })}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Chat Input Bar */}
              <div className="p-3 bg-slate-850 border-t border-slate-800 flex items-center gap-2">
                <input
                  type="text"
                  value={userInput}
                  onChange={(e) => setUserInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder={
                    fsmState === 'entering_data'
                      ? 'أدخل البيانات المطلوبة هنا...'
                      : 'أرسل رسالة للبوت (مثل /start أو /admin)...'
                  }
                  className="flex-1 bg-slate-900 border border-slate-700 text-slate-100 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-amber-500 transition"
                />
                <button
                  onClick={() => handleSendMessage()}
                  className="bg-amber-500 hover:bg-amber-400 text-slate-950 p-2.5 rounded-xl shadow font-bold transition flex items-center justify-center"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Quick Test Panel & Database Control */}
            <div className="lg:col-span-5 flex flex-col gap-6">
              {/* Database Live Products Quick Selector */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
                <h3 className="font-bold text-base text-slate-100 flex items-center gap-2 border-b border-slate-800 pb-3">
                  <Sliders className="w-5 h-5 text-amber-500" />
                  <span>المنتجات الحية (من SQLite)</span>
                </h3>

                <div className="space-y-2.5">
                  <p className="text-xs text-slate-400">انقر لتجربة شحن أي منتج مباشرة في البوت:</p>

                  <div className="grid grid-cols-2 gap-2">
                    {products.map((prod) => {
                      const IconComp = getProductIcon(prod.key);
                      return (
                        <button
                          key={prod.key}
                          onClick={() => handleButtonClick(`prod:${prod.key}`)}
                          className="p-3 bg-slate-800/80 hover:bg-slate-800 border border-slate-700/60 rounded-xl text-xs font-semibold text-amber-400 flex items-center gap-2 text-right transition"
                        >
                          <IconComp className="w-4 h-4 text-amber-500 shrink-0" />
                          <div className="truncate">
                            <div className="truncate">{prod.name}</div>
                            <div className="text-[10px] text-slate-400 font-normal truncate">
                              {prod.packages ? `${prod.packages.length} باقات` : 'باقات'}
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>

                  <div className="pt-2 border-t border-slate-800/80 flex gap-2">
                    <button
                      onClick={() => handleSendMessage('/admin')}
                      className="flex-1 py-2.5 px-3 bg-amber-500/10 border border-amber-500/40 text-amber-400 hover:bg-amber-500/20 text-xs font-bold rounded-xl transition flex items-center justify-center gap-1.5"
                    >
                      <UserCheck className="w-4 h-4" />
                      <span>فتح لوحة الأدمن /admin</span>
                    </button>

                    <button
                      onClick={() => handleButtonClick('user:my_orders')}
                      className="flex-1 py-2.5 px-3 bg-slate-800 border border-slate-700 text-slate-200 hover:bg-slate-750 text-xs font-bold rounded-xl transition flex items-center justify-center gap-1.5"
                    >
                      <ShoppingBag className="w-4 h-4" />
                      <span>عرض طلباتي</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* TON Rate Instant Manager Card */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3.5 shadow-xl">
                <div className="flex items-center justify-between">
                  <h3 className="font-bold text-sm text-slate-100 flex items-center gap-2">
                    <RefreshCw className="w-4 h-4 text-amber-500" />
                    <span>سعر صرف العملة (TON / EGP)</span>
                  </h3>
                  <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 font-bold border border-amber-500/20">
                    تحديث فورى API
                  </span>
                </div>

                <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800/80 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400">سعر TON الحالي:</span>
                    <span className="text-sm font-bold text-amber-400 font-mono">
                      {settings.ton_egp_rate || '120.0'} EGP
                    </span>
                  </div>
                  <div className="flex items-center justify-between pt-1.5 border-t border-slate-900 text-[11px]">
                    <span className="text-slate-400">آخر تحديث للسعر:</span>
                    <span className="text-slate-300 font-mono dir-ltr">
                      {settings.ton_rate_updated_at || 'غير محدد'}
                    </span>
                  </div>
                </div>

                <button
                  onClick={handleRefreshTonRate}
                  disabled={isRefreshingRate}
                  className="w-full py-2.5 bg-amber-500 hover:bg-amber-400 disabled:bg-slate-800 text-slate-950 disabled:text-slate-500 font-bold text-xs rounded-xl transition shadow flex items-center justify-center gap-2"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isRefreshingRate ? 'animate-spin' : ''}`} />
                  <span>{isRefreshingRate ? 'جاري التحديث من الـ API...' : 'تحديث سعر TON فورًا من الـ API'}</span>
                </button>
              </div>

              {/* Customer Ratings Analytics Card */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-xl">
                <div className="flex items-center justify-between">
                  <h3 className="font-bold text-sm text-slate-100 flex items-center gap-2">
                    <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
                    <span>تقييمات المتجر ومتوسط آراء العملاء</span>
                  </h3>
                  <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 font-bold border border-amber-500/20">
                    SQLite Live
                  </span>
                </div>

                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-baseline gap-2">
                        <span className="text-3xl font-extrabold text-amber-400 font-mono">
                          {dbStats.avg_rating || '5.0'}
                        </span>
                        <span className="text-xs text-slate-400 font-medium">/ 5.0</span>
                      </div>
                      <div className="flex items-center gap-1 mt-1">
                        {[1, 2, 3, 4, 5].map((s) => (
                          <Star
                            key={s}
                            className={`w-3.5 h-3.5 ${
                              s <= Math.round(dbStats.avg_rating || 5)
                                ? 'text-amber-400 fill-amber-400'
                                : 'text-slate-700'
                            }`}
                          />
                        ))}
                      </div>
                    </div>

                    <div className="text-left bg-slate-900/80 px-3 py-2 rounded-lg border border-slate-800">
                      <div className="text-xs font-bold text-slate-200 font-mono">
                        {dbStats.total_ratings || 0}
                      </div>
                      <div className="text-[10px] text-slate-400">تقييمات مسجلة</div>
                    </div>
                  </div>

                  {/* Rating Breakdown Progress Bars */}
                  <div className="space-y-1.5 pt-2 border-t border-slate-900">
                    {[5, 4, 3, 2, 1].map((starNum) => {
                      const count = dbStats.ratings_breakdown?.[String(starNum)] || 0;
                      const total = dbStats.total_ratings || 1;
                      const pct = Math.min(100, Math.round((count / (total || 1)) * 100));
                      return (
                        <div key={starNum} className="flex items-center gap-2 text-[11px]">
                          <span className="w-8 text-slate-400 font-medium flex items-center gap-0.5 dir-ltr justify-end">
                            {starNum} <Star className="w-2.5 h-2.5 text-amber-400 inline fill-amber-400" />
                          </span>
                          <div className="flex-1 h-1.5 bg-slate-900 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-amber-400 rounded-full transition-all duration-500"
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                          <span className="w-6 text-slate-500 font-mono text-left">{count}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => handleButtonClick('rate_ord:GZ-10024:5')}
                    className="flex-1 py-2 px-2 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-300 font-bold text-xs rounded-xl transition flex items-center justify-center gap-1"
                  >
                    <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                    <span>تجربة تقييم 5 نجوم ⭐</span>
                  </button>
                  <button
                    onClick={fetchDbStats}
                    className="py-2 px-3 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold rounded-xl transition flex items-center gap-1"
                  >
                    <RefreshCw className="w-3 h-3" />
                  </button>
                </div>
              </div>

              {/* Order Status Toast Notifications Simulator Card */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3.5 shadow-xl">
                <div className="flex items-center justify-between">
                  <h3 className="font-bold text-sm text-slate-100 flex items-center gap-2">
                    <BellRing className="w-4 h-4 text-amber-500" />
                    <span>تنبيهات حالة الطلب (Toast Notifications)</span>
                  </h3>
                  <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-bold border border-emerald-500/20">
                    نشط تلقائيًا
                  </span>
                </div>

                <p className="text-xs text-slate-400 leading-relaxed">
                  تظهر التنبيهات المباشرة فور تغيير حالة أي طلب في قاعدة البيانات من <b>'قيد المراجعة'</b> إلى <b>'مكتمل'</b> أو <b>'مرفوض'</b>:
                </p>

                <div className="grid grid-cols-2 gap-2 pt-1">
                  <button
                    onClick={() => {
                      addToast({
                        title: '✅ تم اكتمال الطلب بنجاح',
                        message: 'تغيرت حالة الطلب #GZ-10024 من "قيد المراجعة" إلى "مكتمل".',
                        type: 'success',
                        orderNumber: 'GZ-10024',
                        oldStatus: 'قيد المراجعة',
                        newStatus: 'مكتمل',
                      });
                    }}
                    className="p-2.5 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 font-bold text-xs rounded-xl transition flex items-center justify-center gap-1.5"
                  >
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span>تنبيه: مكتمل ✅</span>
                  </button>

                  <button
                    onClick={() => {
                      addToast({
                        title: '❌ تم رفض الطلب',
                        message: 'تغيرت حالة الطلب #GZ-10024 من "قيد المراجعة" إلى "مرفوض".',
                        type: 'error',
                        orderNumber: 'GZ-10024',
                        oldStatus: 'قيد المراجعة',
                        newStatus: 'مرفوض',
                      });
                    }}
                    className="p-2.5 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-300 font-bold text-xs rounded-xl transition flex items-center justify-center gap-1.5"
                  >
                    <XCircle className="w-4 h-4 text-rose-400" />
                    <span>تنبيه: مرفوض ❌</span>
                  </button>
                </div>
              </div>

              {/* Bot Architecture Features Card */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
                <h3 className="font-bold text-sm text-slate-200 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  <span>المواصفات المنفذة بقاعدة البيانات</span>
                </h3>

                <ul className="text-xs text-slate-300 space-y-2">
                  <li className="flex items-start gap-2">
                    <span className="text-amber-500">▪</span>
                    <span><b>aiogram 3.x Router & FSM</b>: تنظيم المشروع في وحدات مستقلة.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-amber-500">▪</span>
                    <span><b>تأكيد دفع TON إلكترونيًا</b>: فحص On-Chain عبر TONAPI وحفظ transaction_hash.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-amber-500">▪</span>
                    <span><b>مهلة 20 دقيقة (APScheduler)</b>: جدولة الفحص والمراجعة الآلية للطلبات.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-amber-500">▪</span>
                    <span><b>قاعدة بيانات حقيقية SQLite</b>: حفظ المستخدمين، الباقات، الطلبات وإعدادات الدفع.</span>
                  </li>
                </ul>
              </div>

            {/* Live SQLite Orders & Payment Proof Screenshots Control Board */}
            <div className="lg:col-span-12 bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-5 shadow-2xl mt-4">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
                <div>
                  <h3 className="font-extrabold text-base text-slate-100 flex items-center gap-2.5">
                    <FileCheck className="w-5 h-5 text-amber-400" />
                    <span>سجل طلبات العملاء وإثباتات الدفع بالصور (SQLite Realtime)</span>
                  </h3>
                  <p className="text-xs text-slate-400 mt-1">
                    يمكن للأدمن معاينة جميع بيانات العميل، صور السكرين شوت، حالة الحساب، والاعتماد أو الرفض
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 font-bold border border-amber-500/30">
                    {allOrders.length} طلبات مسجلة
                  </span>
                  <button
                    onClick={() => {
                      fetchAllOrders();
                      fetchDbStats();
                      addToast({ title: '🔄 تم تحديث الطلبات', message: 'تم تحديث قائمة الطلبات من قاعدة البيانات.', type: 'info' });
                    }}
                    className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition"
                    title="تحديث البيانات"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Search & Filter Options */}
              <div className="flex flex-col md:flex-row gap-3">
                <div className="relative flex-1">
                  <Search className="w-4 h-4 text-slate-500 absolute right-3.5 top-3" />
                  <input
                    type="text"
                    value={orderSearchTerm}
                    onChange={(e) => setOrderSearchTerm(e.target.value)}
                    placeholder="بحث برقم الطلب، اسم العميل، اليوزر نيم، أو آيدي اللعبة..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pr-10 pl-4 py-2.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500 transition"
                  />
                  {orderSearchTerm && (
                    <button
                      onClick={() => setOrderSearchTerm('')}
                      className="absolute left-3 top-3 text-slate-500 hover:text-white"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                {/* Status Filter Tabs */}
                <div className="flex items-center gap-1.5 overflow-x-auto pb-1 custom-scrollbar">
                  {[
                    { key: 'all', label: 'الكل', count: allOrders.length },
                    { key: 'payment_review', label: '🔍 قيد المراجعة', count: allOrders.filter(o => o.status === 'payment_review').length },
                    { key: 'pending_payment', label: '⏳ بانتظار الدفع', count: allOrders.filter(o => o.status === 'pending_payment').length },
                    { key: 'completed', label: '✅ مكتمل', count: allOrders.filter(o => o.status === 'completed').length },
                    { key: 'rejected', label: '❌ مرفوض', count: allOrders.filter(o => o.status === 'rejected').length },
                  ].map((tab) => (
                    <button
                      key={tab.key}
                      onClick={() => setOrderFilterStatus(tab.key)}
                      className={`px-3 py-2 rounded-xl text-xs font-bold transition whitespace-nowrap flex items-center gap-1.5 ${
                        orderFilterStatus === tab.key
                          ? 'bg-amber-500 text-slate-950 shadow'
                          : 'bg-slate-950 text-slate-300 hover:bg-slate-800 border border-slate-800'
                      }`}
                    >
                      <span>{tab.label}</span>
                      <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                        orderFilterStatus === tab.key ? 'bg-slate-950/20 text-slate-950' : 'bg-slate-800 text-slate-400'
                      }`}>
                        {tab.count}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Orders Grid List */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {allOrders.filter((ord) => {
                  const search = orderSearchTerm.toLowerCase();
                  const matchSearch =
                    !search ||
                    String(ord.order_number || '').toLowerCase().includes(search) ||
                    String(ord.customer_data || '').toLowerCase().includes(search) ||
                    String(ord.full_name || '').toLowerCase().includes(search) ||
                    String(ord.username || '').toLowerCase().includes(search) ||
                    String(ord.user_id || ord.telegram_id || '').includes(search);

                  const matchStatus = orderFilterStatus === 'all' || ord.status === orderFilterStatus;
                  return matchSearch && matchStatus;
                }).length === 0 ? (
                  <div className="col-span-full bg-slate-950/60 border border-slate-800/80 rounded-2xl p-8 text-center text-slate-400 text-xs space-y-2">
                    <FileText className="w-8 h-8 text-slate-600 mx-auto" />
                    <div>لا توجد طلبات تطابق خيارات البحث المحددة.</div>
                  </div>
                ) : (
                  allOrders.filter((ord) => {
                    const search = orderSearchTerm.toLowerCase();
                    const matchSearch =
                      !search ||
                      String(ord.order_number || '').toLowerCase().includes(search) ||
                      String(ord.customer_data || '').toLowerCase().includes(search) ||
                      String(ord.full_name || '').toLowerCase().includes(search) ||
                      String(ord.username || '').toLowerCase().includes(search) ||
                      String(ord.user_id || ord.telegram_id || '').includes(search);

                    const matchStatus = orderFilterStatus === 'all' || ord.status === orderFilterStatus;
                    return matchSearch && matchStatus;
                  }).map((ord) => {
                    const statusBadge =
                      ord.status === 'completed' ? { label: '✅ مكتمل', bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' } :
                      ord.status === 'rejected' ? { label: '❌ مرفوض', bg: 'bg-rose-500/10 text-rose-400 border-rose-500/20' } :
                      ord.status === 'processing' ? { label: '⚙️ قيد التنفيذ', bg: 'bg-blue-500/10 text-blue-400 border-blue-500/20' } :
                      ord.status === 'payment_review' ? { label: '🔍 قيد المراجعة', bg: 'bg-amber-500/10 text-amber-400 border-amber-500/20' } :
                      { label: '⏳ في انتظار الدفع', bg: 'bg-slate-800 text-slate-400 border-slate-700' };

                    return (
                      <div
                        key={ord.order_number || ord.id}
                        className="bg-slate-950 border border-slate-800/90 rounded-2xl p-4 space-y-3.5 hover:border-slate-700 transition shadow-lg flex flex-col justify-between"
                      >
                        <div className="space-y-3">
                          {/* Order Card Header */}
                          <div className="flex items-center justify-between border-b border-slate-900 pb-2.5">
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-sm font-extrabold text-amber-400">
                                #{ord.order_number}
                              </span>
                              <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${statusBadge.bg}`}>
                                {statusBadge.label}
                              </span>
                            </div>
                            <span className="text-[10px] text-slate-500 font-mono dir-ltr">{ord.created_at}</span>
                          </div>

                          {/* Customer Info Row */}
                          <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800/60 space-y-1.5">
                            <div className="flex items-center justify-between text-xs">
                              <span className="text-slate-400 flex items-center gap-1 font-medium">
                                <User className="w-3.5 h-3.5 text-amber-500" />
                                <span>مقدم الطلب:</span>
                              </span>
                              <span className="font-bold text-slate-100">{ord.full_name || 'عميل GameZone'}</span>
                            </div>
                            <div className="flex items-center justify-between text-[11px]">
                              <span className="text-slate-400">اليوزر / Telegram ID:</span>
                              <div className="flex items-center gap-1.5 font-mono">
                                <span className="text-amber-400 font-bold">@{ord.username || 'بدون'}</span>
                                <span className="text-slate-500 text-[10px]">({ord.user_id || ord.telegram_id || '102938475'})</span>
                              </div>
                            </div>
                          </div>

                          {/* Order Details Summary */}
                          <div className="space-y-1.5 text-xs">
                            <div className="flex justify-between">
                              <span className="text-slate-400">المنتج والباكة:</span>
                              <span className="font-semibold text-slate-200">{ord.product_name} - {ord.package_name}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-400">المبلغ ووسيلة الدفع:</span>
                              <div className="flex items-center gap-1.5 font-mono">
                                <span className="font-bold text-emerald-400">{ord.price_egp} EGP</span>
                                <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-900 text-amber-300 font-bold uppercase border border-slate-800">
                                  {ord.payment_method}
                                </span>
                              </div>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-400">آيدي اللعبة / الحساب:</span>
                              <span className="font-mono text-slate-200 font-bold bg-slate-900 px-2 py-0.5 rounded border border-slate-800/80">
                                {ord.customer_data}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-400">المرجع / Memo:</span>
                              <span className="font-mono text-amber-400 font-bold">
                                {ord.memo || ord.receipt_file_id || 'GZ-PROOF-1002'}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Action Bar & Screenshot Preview Button */}
                        <div className="pt-2 border-t border-slate-900 space-y-2">
                          <button
                            onClick={() => setSelectedProofOrder(ord)}
                            className="w-full py-2 px-3 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-300 font-bold text-xs rounded-xl transition flex items-center justify-center gap-1.5"
                          >
                            <ImageIcon className="w-4 h-4 text-amber-400" />
                            <span>📸 معاينة صورة الإثبات والبيانات الكاملة</span>
                          </button>

                          <div className="flex gap-2">
                            <button
                              onClick={() => {
                                handleButtonClick(`adm_approve:${ord.order_number}`);
                              }}
                              className="flex-1 py-2 bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/40 text-emerald-300 font-bold text-xs rounded-xl transition flex items-center justify-center gap-1"
                            >
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                              <span>قبول ✅</span>
                            </button>

                            <button
                              onClick={() => {
                                handleButtonClick(`adm_reject:${ord.order_number}`);
                              }}
                              className="flex-1 py-2 bg-rose-600/20 hover:bg-rose-600/30 border border-rose-500/40 text-rose-300 font-bold text-xs rounded-xl transition flex items-center justify-center gap-1"
                            >
                              <XCircle className="w-3.5 h-3.5 text-rose-400" />
                              <span>رفض ❌</span>
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
            </div>
          </div>
        )}

        {/* Tab 2: Python Code Inspector */}
        {activeTab === 'files' && (
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 bg-slate-900 border border-slate-800 rounded-2xl p-4 min-h-[700px]">
            {/* File List Tree Sidebar */}
            <div className="md:col-span-4 border-l border-slate-800 pl-4 space-y-1 overflow-y-auto max-h-[700px] custom-scrollbar">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider px-3 py-2 border-b border-slate-800 mb-2">
                شجرة ملفات المشروع ({fileList.length} ملفًا)
              </h3>
              {fileList.map((file) => (
                <button
                  key={file}
                  onClick={() => setSelectedFile(file)}
                  className={`w-full text-right px-3 py-2 rounded-xl text-xs font-mono transition flex items-center justify-between ${
                    selectedFile === file
                      ? 'bg-amber-500/15 border border-amber-500/40 text-amber-400 font-semibold'
                      : 'text-slate-300 hover:bg-slate-800/60'
                  }`}
                >
                  <span className="truncate">{file}</span>
                  <ChevronRight className="w-3.5 h-3.5 text-slate-500" />
                </button>
              ))}
            </div>

            {/* Code Viewer Panel */}
            <div className="md:col-span-8 flex flex-col space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-amber-500" />
                  <span className="font-mono text-sm text-amber-400 font-bold">{selectedFile}</span>
                </div>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(fileContents[selectedFile] || '');
                  }}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-750 text-slate-300 text-xs rounded-lg flex items-center gap-1.5 transition"
                >
                  <Copy className="w-3.5 h-3.5" />
                  <span>نسخ الكود</span>
                </button>
              </div>

              <pre className="flex-1 bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs text-slate-200 overflow-x-auto overflow-y-auto max-h-[620px] leading-relaxed custom-scrollbar dir-ltr">
                <code>{fileContents[selectedFile] || '# جار التحميل...'}</code>
              </pre>
            </div>
          </div>
        )}

        {/* Tab 3: .Env & Bot Configuration */}
        {activeTab === 'config' && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6 max-w-4xl mx-auto w-full">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                  <Settings className="w-5 h-5 text-amber-500" />
                  <span>إعدادات ملف البيئة .env</span>
                </h2>
                <p className="text-xs text-slate-400">
                  قم بضبط BOT_TOKEN و ADMIN_ID ومحفظة TON قبل التشغيل
                </p>
              </div>
              <button
                onClick={handleSaveEnv}
                className="bg-amber-500 hover:bg-amber-400 text-slate-950 px-5 py-2.5 rounded-xl font-bold text-sm shadow transition flex items-center gap-2"
              >
                <Copy className="w-4 h-4" />
                <span>حفظ التغييرات</span>
              </button>
            </div>

            {savedSuccess && (
              <div className="bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-sm px-4 py-3 rounded-xl flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <span>تم حفظ التعديلات بنجاح في ملف .env</span>
              </div>
            )}

            <div className="space-y-3">
              <label className="text-xs font-bold text-slate-300 block">محتوى ملف .env:</label>
              <textarea
                value={envContent}
                onChange={(e) => setEnvContent(e.target.value)}
                rows={12}
                className="w-full bg-slate-950 border border-slate-800 text-amber-300 font-mono text-xs rounded-xl p-4 focus:outline-none focus:border-amber-500 dir-ltr leading-relaxed"
              />
            </div>

            <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3">
              <h4 className="font-bold text-sm text-slate-200 flex items-center gap-2">
                <Terminal className="w-4 h-4 text-amber-500" />
                <span>أمر تشغيل البوت محليًا</span>
              </h4>
              <div className="bg-slate-900 border border-slate-800 p-3 rounded-lg font-mono text-xs text-slate-300 flex items-center justify-between dir-ltr">
                <code>python main.py</code>
                <button
                  onClick={() => navigator.clipboard.writeText('python main.py')}
                  className="text-slate-400 hover:text-white text-xs px-2 py-1 rounded bg-slate-800"
                >
                  نسخ
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Selected Payment Proof Screenshot Inspector Modal */}
        {selectedProofOrder && (
          <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto animate-fade-in dir-rtl">
            <div className="bg-slate-900 border border-slate-800 w-full max-w-2xl rounded-3xl shadow-2xl overflow-hidden flex flex-col my-auto max-h-[92vh]">
              {/* Modal Header */}
              <div className="bg-slate-850 px-6 py-4 border-b border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
                    <ImageIcon className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-base text-slate-100 flex items-center gap-2">
                      <span>معاينة إثبات التحويل والمعلومات الكاملة</span>
                      <span className="text-xs px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-mono font-bold">
                        #{selectedProofOrder.order_number}
                      </span>
                    </h3>
                    <p className="text-xs text-slate-400">مراجعة سكرين شوت التحويل وتأكيد بيانات العميل</p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedProofOrder(null)}
                  className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Modal Body */}
              <div className="p-6 overflow-y-auto space-y-6 custom-scrollbar">
                {/* Top Proof Screenshot Card */}
                <div className="bg-slate-950 rounded-2xl p-4 border border-slate-800/90 flex flex-col items-center justify-center">
                  <div className="text-xs text-slate-400 font-semibold mb-3 flex items-center justify-between w-full px-2 border-b border-slate-900 pb-2">
                    <span className="flex items-center gap-1.5 text-emerald-400 font-bold">
                      <CheckCircle2 className="w-4 h-4" />
                      <span>صورة إثبات التحويل السكرين شوت ({selectedProofOrder.payment_method?.toUpperCase()})</span>
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono dir-ltr">{selectedProofOrder.created_at}</span>
                  </div>
                  <img
                    src={generateProofImageUrl(selectedProofOrder)}
                    alt="Payment Receipt Screenshot"
                    className="w-full max-w-md h-auto rounded-xl border border-slate-800 shadow-xl object-contain bg-slate-900"
                  />
                </div>

                {/* Customer & Order Details Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Customer Info Box */}
                  <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 space-y-3">
                    <h4 className="font-bold text-xs text-amber-400 flex items-center gap-1.5 border-b border-slate-900 pb-2">
                      <User className="w-4 h-4 text-amber-400" />
                      <span>بيانات العميل (مقدم الطلب)</span>
                    </h4>
                    <div className="text-xs space-y-2 text-slate-300">
                      <div className="flex justify-between">
                        <span className="text-slate-400">الاسم الكامل:</span>
                        <span className="font-bold text-slate-100">{selectedProofOrder.full_name || 'عميل GameZone'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">اسم المستخدم:</span>
                        <span className="font-mono text-amber-400 font-bold">@{selectedProofOrder.username || 'بدون_يوزر'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Telegram ID:</span>
                        <span className="font-mono text-slate-200">{selectedProofOrder.user_id || selectedProofOrder.telegram_id || '102938475'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">حالة الحساب:</span>
                        <span className={`font-bold ${selectedProofOrder.is_banned ? 'text-rose-400' : 'text-emerald-400'}`}>
                          {selectedProofOrder.is_banned ? '🔴 محظور' : '🟢 حساب نشط'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Order Details Box */}
                  <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 space-y-3">
                    <h4 className="font-bold text-xs text-amber-400 flex items-center gap-1.5 border-b border-slate-900 pb-2">
                      <ShoppingBag className="w-4 h-4 text-amber-400" />
                      <span>تفاصيل المنتج والشحن</span>
                    </h4>
                    <div className="text-xs space-y-2 text-slate-300">
                      <div className="flex justify-between">
                        <span className="text-slate-400">المنتج والباقة:</span>
                        <span className="font-bold text-slate-100">{selectedProofOrder.product_name} - {selectedProofOrder.package_name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">المبلغ المطلوب:</span>
                        <span className="font-bold text-emerald-400 font-mono">{selectedProofOrder.price_egp} EGP</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">وسيلة الدفع:</span>
                        <span className="font-bold text-amber-300 uppercase">{selectedProofOrder.payment_method}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">الـ Memo / المرجع:</span>
                        <span className="font-mono text-amber-400 font-bold">{selectedProofOrder.memo || selectedProofOrder.receipt_file_id || 'GZ-PROOF-9931'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">آيدي اللاعب:</span>
                        <span className="font-mono text-slate-100 font-bold bg-slate-900 px-2 py-0.5 rounded border border-slate-800">{selectedProofOrder.customer_data}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">تقييم العميل:</span>
                        <span className="font-bold text-amber-300">
                          {selectedProofOrder.rating ? `⭐ ${selectedProofOrder.rating}/5` : 'لم يتم التقييم بعد'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Modal Actions Footer */}
              <div className="bg-slate-850 p-4 border-t border-slate-800 flex gap-3">
                <button
                  onClick={() => {
                    handleButtonClick(`adm_approve:${selectedProofOrder.order_number}`);
                    setSelectedProofOrder(null);
                  }}
                  className="flex-1 py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow transition flex items-center justify-center gap-2"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>✅ قبول واكتمال الطلب</span>
                </button>

                <button
                  onClick={() => {
                    handleButtonClick(`adm_reject:${selectedProofOrder.order_number}`);
                    setSelectedProofOrder(null);
                  }}
                  className="flex-1 py-3 bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs rounded-xl shadow transition flex items-center justify-center gap-2"
                >
                  <XCircle className="w-4 h-4" />
                  <span>❌ رفض الطلب</span>
                </button>

                <button
                  onClick={() => setSelectedProofOrder(null)}
                  className="py-3 px-5 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs rounded-xl transition"
                >
                  إغلاق
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
