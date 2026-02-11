import { Trophy, Zap, Coins, TrendingUp } from 'lucide-react'
import { useState } from 'react'

export default function GamificationPanel({ profile, loading }) {
  const [showBadges, setShowBadges] = useState(false)

  if (loading || !profile) {
    return (
      <div className="flex items-center gap-4">
        <div className="h-12 w-32 bg-dark-700 rounded-lg animate-pulse"></div>
      </div>
    )
  }

  const { xp, coins, level, badges } = profile

  // Calcular XP para el siguiente nivel
  const xpForCurrentLevel = Math.pow(level - 1, 2) * 100
  const xpForNextLevel = Math.pow(level, 2) * 100
  const xpProgress = xp - xpForCurrentLevel
  const xpNeeded = xpForNextLevel - xpForCurrentLevel
  const progressPercentage = Math.min((xpProgress / xpNeeded) * 100, 100)

  return (
    <div className="flex items-center gap-6">
      {/* XP y Nivel */}
      <div className="flex items-center gap-4">
        <div className="relative">
          <div className="w-16 h-16 bg-gradient-to-br from-primary-500 to-primary-600 rounded-full flex items-center justify-center shadow-lg shadow-primary-500/30 border-2 border-dark-800">
            <span className="text-xl font-bold text-white">{level}</span>
          </div>
          <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-primary-400 rounded-full flex items-center justify-center border-2 border-dark-800">
            <Zap className="w-3 h-3 text-white" />
          </div>
        </div>
        
        <div className="min-w-[200px]">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-dark-400 font-medium">Nivel {level}</span>
            <span className="text-xs text-primary-400 font-bold">{xp} XP</span>
          </div>
          <div className="progress-bar">
            <div 
              className="progress-fill"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
          <div className="text-xs text-dark-500 mt-1">
            {xpNeeded - xpProgress} XP para nivel {level + 1}
          </div>
        </div>
      </div>

      {/* UrbanCoins */}
      <div className="flex items-center gap-2 bg-dark-800 px-4 py-2 rounded-lg border border-dark-700">
        <Coins className="w-5 h-5 text-warning-400" />
        <span className="text-sm font-bold text-warning-400">{coins}</span>
        <span className="text-xs text-dark-400">Coins</span>
      </div>

      {/* Insignias */}
      <div className="relative">
        <button
          onClick={() => setShowBadges(!showBadges)}
          className="relative p-2 bg-dark-800 hover:bg-dark-700 rounded-lg border border-dark-700 transition-colors"
          aria-label="Ver insignias"
        >
          <Trophy className="w-5 h-5 text-warning-400" />
          {badges.length > 0 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-primary-500 rounded-full flex items-center justify-center text-xs font-bold text-white">
              {badges.length}
            </span>
          )}
        </button>

        {/* Dropdown de insignias */}
        {showBadges && (
          <>
            <div 
              className="fixed inset-0 z-40" 
              onClick={() => setShowBadges(false)}
            />
            <div className="absolute right-0 top-full mt-2 w-64 bg-dark-800 border border-dark-700 rounded-xl shadow-2xl z-50 p-4">
              <div className="flex items-center gap-2 mb-3">
                <Trophy className="w-5 h-5 text-warning-400" />
                <h3 className="font-bold text-white">Insignias</h3>
              </div>
              {badges.length === 0 ? (
                <p className="text-sm text-dark-400 text-center py-4">
                  Aún no has ganado insignias
                </p>
              ) : (
                <div className="space-y-2">
                  {badges.map((badge, index) => (
                    <div
                      key={index}
                      className="flex items-center gap-3 p-2 bg-dark-700 rounded-lg border border-dark-600"
                    >
                      <div className="w-8 h-8 bg-gradient-to-br from-warning-400 to-warning-500 rounded-full flex items-center justify-center">
                        <Trophy className="w-4 h-4 text-white" />
                      </div>
                      <span className="text-sm text-dark-100 font-medium">{badge}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
