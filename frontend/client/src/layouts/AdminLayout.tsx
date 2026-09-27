import React, { useMemo } from "react";
import {
  BarChart2,
  Brain,
  Building2,
  CalendarRange,
  FileBarChart,
  LayoutDashboard,
  TrendingUp,
  Users,
  UserRound,
  Zap,
  Compass,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useTranslation } from "@/i18n";
import { DashboardShell, DashboardNavItem, DashboardRoleTheme } from "./DashboardShell";

interface AdminLayoutProps {
  children: React.ReactNode;
  activePage: string;
  onNavigate: (page: string) => void;
}

const ADMIN_ROLE_THEME: DashboardRoleTheme = {
  activeNavBg: "bg-purple-50",
  activeNavText: "text-[#7c3aed]",
  activeIndicator: "bg-[#7c3aed]",
  hoverNavBg: "hover:bg-purple-50/50 hover:text-[#7c3aed]",
  avatarBg: "bg-purple-100 text-[#7c3aed]",
  badgeDotBg: "bg-purple-500",
  headerTitleColor: "text-[#123057]",
};

export function AdminLayout({ children, activePage, onNavigate }: AdminLayoutProps) {
  const { user } = useAuth();
  const { isHindi } = useTranslation();

  const navItems: DashboardNavItem[] = useMemo(
    () => [
      { id: "Dashboard", label: isHindi ? "डैशबोर्ड" : "Dashboard", icon: LayoutDashboard },
      { id: "Workforce Intelligence", label: isHindi ? "कार्यबल इंटेलिजेंस" : "Workforce Intelligence", icon: Building2 },
      { id: "Workforce Overview", label: isHindi ? "कार्यबल अवलोकन" : "Workforce Overview", icon: Building2 },
      { id: "Competency Analytics", label: isHindi ? "क्षमता विश्लेषण" : "Competency Analytics", icon: BarChart2 },
      { id: "Skill Gap Analytics", label: isHindi ? "कौशल अंतराल विश्लेषण" : "Skill Gap Analytics", icon: Brain },
      { id: "Training Effectiveness", label: isHindi ? "प्रशिक्षण प्रभावशीलता" : "Training Effectiveness", icon: TrendingUp },
      { id: "Emerging Skills", label: isHindi ? "उभरते कौशल" : "Emerging Skills", icon: Zap },
      { id: "Capacity Planning", label: isHindi ? "क्षमता योजना" : "Capacity Planning", icon: CalendarRange },
      { id: "Opportunity Network", label: isHindi ? "अवसर नेटवर्क" : "Opportunity Network", icon: Compass },
      { id: "Talent Discovery", label: isHindi ? "प्रतिभा खोज" : "Talent Discovery", icon: Compass },
      { id: "Users", label: isHindi ? "उपयोगकर्ता पंजी" : "Users", icon: Users },
      { id: "Reports", label: isHindi ? "प्रशासकीय रिपोर्ट" : "Reports", icon: FileBarChart },
      { id: "Profile", label: isHindi ? "प्रोफ़ाइल" : "Profile", icon: UserRound },
    ],
    [isHindi]
  );

  return (
    <DashboardShell
      activePage={activePage}
      onNavigate={onNavigate}
      navItems={navItems}
      workspaceTitle={isHindi ? "प्रशासक कार्यक्षेत्र" : "ADMIN WORKSPACE"}
      headerWorkspaceLabel={isHindi ? "शिक्षासेतु कार्यक्षेत्र" : "SHIKSHASETU WORKSPACE"}
      logoHref="/admin"
      roleBadgeText="Director (Capability & Human Resources)"
      userDisplayName={user?.full_name || "System Administrator"}
      userRoleSubtitle="Director (Capability & Human Resources)"
      bgClassName="bg-[#f4f7fb]"
      roleTheme={ADMIN_ROLE_THEME}
    >
      {children}
    </DashboardShell>
  );
}

export default AdminLayout;
