import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { CountryView } from "@/components/data/country-view";

const ISO2 = /^[A-Za-z]{2}$/;

interface Props {
  params: Promise<{ code: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { code } = await params;
  return { title: ISO2.test(code) ? code.toUpperCase() : "Country" };
}

export default async function CountryPage({ params }: Props) {
  const { code } = await params;
  if (!ISO2.test(code)) notFound();
  return <CountryView iso2={code.toUpperCase()} />;
}
