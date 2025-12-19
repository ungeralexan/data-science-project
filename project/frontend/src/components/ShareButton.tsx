import { ShareAltOutlined } from "@ant-design/icons";
import "./css/ShareButton.css";

type Props = {
  title: string;
  url: string;
  size?: "small" | "default";
};

export default function ShareButton({ title, url, size = "default" }: Props) {
  const sizeClass = size === "small" ? "share-button--small" : "";

  const handleShare = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    e.preventDefault();

    const shareData = {
      title,
      text: title,
      url,
    };

    // Use native share ONLY if it is truly supported
    const canShare =
      typeof navigator !== "undefined" &&
      typeof navigator.share === "function" &&
      (
        typeof (navigator as any).canShare !== "function" ||
        (navigator as any).canShare(shareData)
      );

    if (canShare) {
      try {
        await navigator.share(shareData);
        return; // real native share happened
      } catch (err) {
        // user cancelled or native share failed → fallback
        console.warn("Native share cancelled/failed, falling back:", err);
      }
    }

    // ---------- FALLBACK ----------
    try {
      await navigator.clipboard.writeText(url);
      alert("Link copied!");
    } catch (err) {
      console.warn("Clipboard failed, using prompt:", err);
      window.prompt("Copy this link:", url);
    }
  };

  return (
    <button
      className={`share-button ${sizeClass}`}
      onClick={handleShare}
      aria-label="Share event"
      title="Share event"
      type="button"
    >
      <ShareAltOutlined />
    </button>
  );
}
