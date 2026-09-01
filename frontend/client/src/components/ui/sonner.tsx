import { useTheme } from "next-themes";
import { Toaster as Sonner, type ToasterProps } from "sonner";

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme = "system" } = useTheme();

  return (
    <Sonner
      theme={theme as ToasterProps["theme"]}
      position="bottom-center"
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            "group toast group-[.toaster]:bg-white group-[.toaster]:text-[#123057] group-[.toaster]:border-[#dfe7f0] group-[.toaster]:shadow-xl group-[.toaster]:rounded-2xl group-[.toaster]:font-semibold group-[.toaster]:text-xs group-[.toaster]:px-4 group-[.toaster]:py-3",
          description: "group-[.toast]:text-slate-500",
          actionButton:
            "group-[.toast]:bg-[#087f76] group-[.toast]:text-white",
          cancelButton:
            "group-[.toast]:bg-slate-100 group-[.toast]:text-slate-600",
        },
      }}
      style={
        {
          "--normal-bg": "var(--popover)",
          "--normal-text": "var(--popover-foreground)",
          "--normal-border": "var(--border)",
        } as React.CSSProperties
      }
      {...props}
    />
  );
};

export { Toaster };
