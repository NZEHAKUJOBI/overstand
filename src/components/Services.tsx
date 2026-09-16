import { Reveal } from "./Reveal";
import { SectionHeading } from "./SectionHeading";
import { ServiceIcon } from "./ServiceIcons";
import { services, servicesIntro } from "@/lib/content";

/**
 * The five member service lines, as cards on a navy field.
 *
 * Five does not divide into a three-column grid, so the first card spans two
 * columns at desktop width and carries the lead line — which also puts real
 * estate, the Society's lead offer, at the head of the grid rather than
 * leaving an orphan tile at the foot.
 */
export function Services() {
  return (
    <section id="services" className="bg-navy-950 py-24 text-paper md:py-32">
      <div className="shell">
        <SectionHeading
          eyebrow="What we offer"
          title="A suite of member services"
          lead={servicesIntro}
          tone="dark"
        />

        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {services.map((service, index) => (
            <Reveal
              key={service.title}
              delay={index * 60}
              className={index === 0 ? "lg:col-span-2" : undefined}
            >
              <article className="flex h-full flex-col gap-5 rounded-xl border border-paper/12 bg-paper/[0.04] p-7 transition-colors duration-300 hover:border-gold-500/45 md:p-8">
                <ServiceIcon
                  name={service.icon}
                  className="h-8 w-8 shrink-0 text-gold-400"
                />

                <div>
                  <h3 className="font-display text-[1.25rem] leading-snug text-paper">
                    {service.title}
                  </h3>
                  <p className="mt-3 text-[0.9375rem] leading-[1.7] text-pretty text-paper/65">
                    {service.body}
                  </p>
                </div>
              </article>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
