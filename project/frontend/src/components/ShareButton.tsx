import { ShareAltOutlined } from "@ant-design/icons"; 
import "./css/ShareButton.css";

type Props = {
  title: string;
  url: string;
  size?: "small" | "default";
};

export default function ShareButton({ title, url, size = "default" }: Props) {
  const sizeClass = size === "small" ? "share-button--small" : "";

  const handleShare = async (e: React.MouseEvent) => {
    e.stopPropagation();

    try {
      if (navigator.share) {
        await navigator.share({ title, url });
        return;
      }
    } catch {
      // user cancelled share -> ignore
      return;
    }

    // fallback: copy link
    try {
      await navigator.clipboard.writeText(url);
      alert("Link copied!");
    } catch {
      window.prompt("Copy this link:", url);
    }
  };

  return (
    <button className={`share-button ${sizeClass}`} onClick={handleShare} aria-label="Share event">
      <ShareAltOutlined />
    </button>
  );
}
