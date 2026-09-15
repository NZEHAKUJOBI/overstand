import { Reveal } from "./Reveal";
import { SectionHeading } from "./SectionHeading";
import { ServiceIcon } from "./ServiceIcons";
import { services } from "@/lib/content";

export function Services() {
  return (
    <section id="services" className="shell py-24 md:py-32">
      <Reveal>
        <SectionHeading
          index="05"
          title="Products & Services"
          lead="The Society is multipurpose by design. Member capital is not confined to residential housing — it is deployed across eight lines, so that no single market cycle determines the whole portfolio."
        />
      </Reveal>

      <Reveal delay={80}>
        <ul className="grid gap-x-10 sm:grid-cols-2 lg:grid-cols-4">
          {services.map((service, index) => (
            <li
              key={service.title}
              className="group border-t border-rule pt-7 pb-9"
            >
              <div className="flex items-center justify-between">
                <ServiceIcon
                  name={service.icon}
                  className="h-8 w-8 text-gold-700 transition-colors duration-300 group-hover:text-forest-700"
                />
                <span className="label-sm text-ink-faint">
                  {String(index + 1).padStart(2, "0")}
                </span>
              </div>
              <h3 className="font-display mt-6 text-[1.125rem] leading-snug text-forest-900">
                {service.title}
              </h3>
              <p className="mt-2.5 text-[0.9375rem] leading-relaxed text-ink-soft">
                {service.body}
              </p>
            </li>
          ))}
        </ul>
      </Reveal>
    </section>
  );
}
